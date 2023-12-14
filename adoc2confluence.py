import argparse
from atlassian import Confluence
from bs4 import BeautifulSoup
import os
import sys
import subprocess


def convert_extension(file: str, new_extension: str = "xhtml") -> str:
    """
    Convert the extension of a file to the specified new extension.

    Args:
        file (str): The path to the file.
        new_extension (str, optional): The new extension to use. Defaults to "xhtml".

    Returns:
        str: The modified filename with the new extension.
    """
    filename, _ = os.path.basename(file).split(".")
    return f"{filename}.{new_extension}"


def push_to_confluence(xhtml_file_path: str, space: str, parent_page_id: str, token: str):
    print(f"-> Open {xhtml_file_path} file")
    with open(xhtml_file_path, "r") as f:
        html_content = f.read()

    print("-> Loading default.css")
    with open("/documents/default.css", "r") as f:
        css_content = f.read()

    # To avoid Confluence header conflict
    print("-> Replacing CSS headers...")
    html_content = html_content.replace("#header", "#header-adoc")
    soup = BeautifulSoup(html_content, "html.parser")

    print("-> Upload images...")
    image_urls = []
    image_tags = soup.find_all("img")

    confluence = Confluence(
        url=os.getenv("CONFLUENCE_URL"), 
        token=token
    )

    folder_path = os.path.dirname(xhtml_file_path)
    for img_tag in image_tags:
        img_src = img_tag["src"]
        img_name = os.path.basename(img_src)

        print(img_src)
        print(img_name)
        print(os.path.join(folder_path, img_src))

        with open(os.path.join(folder_path, img_src), "rb") as img_file:
            response = confluence.attach_content(
                page_id=parent_page_id,
                name=img_name,
                content=img_file.read(),
            )

            if response:
                print(f"-> Images {img_name} uploaded.")
                if "results" in response:
                    img_url = response["results"][0]["_links"]["download"]
                else:
                    img_url = response["_links"]["download"]
                image_urls.append((img_src, img_url))
                img_tag["src"] = img_url

    for h1_tag in soup.find_all("h1"):
        h1_tag.extract()

    page_title = soup.find("title").text.strip().title()
    print(f"-> Extract title: {page_title}")
    body_tag = str(soup.find("body"))

    print("-> Building final body")
    body_content = f"""<div>
    <p class="auto-cursor-target">
        <br/>
    </p>
    <ac:structured-macro ac:macro-id="d5e0bec5-bf2c-44d8-a525-93c76adb561e" ac:name="style" ac:schema-version="1">
        <ac:plain-text-body>
            <![CDATA[html {css_content}]]>
        </ac:plain-text-body>
    </ac:structured-macro>
    </div>
    {body_tag}
    """

    existing_page = confluence.get_page_by_title(space=space, title=page_title)

    if existing_page:
        page_id = existing_page['id']

        # if confluence.is_page_content_is_already_updated(page_id, body_content) is True:
        #     print("Confluence page content is already up to date.")
        #     sys.exit("Confluence page content is already up to date.")

        confluence.update_page(
            page_id=page_id,
            title=page_title,
            body=body_content,
        )
        print(f"Confluence page updated (ID : {page_id}) !")
    else:
        page_id = confluence.create_page(
            space=space, 
            title=page_title, 
            body=body_content, 
            parent_id=parent_page_id
        )
        print(f"Confluence page created (ID : {page_id['id']}) !")


parser = argparse.ArgumentParser(description="Convert ASCIIDOC to HTML and send to Confluence.")
parser.add_argument("input_file", help="Path to the input ASCIIDOC file")
parser.add_argument("--space", help="Confluence space key", required=True)
parser.add_argument("--parent_page_id", help="ID of the parent page", required=True)
parser.add_argument("--token", help="Confluence Token API", required=True)

args = parser.parse_args()

folder_path = os.path.dirname(args.input_file)
adoc_file_name = os.path.basename(args.input_file)
xhtml_file_name = convert_extension(adoc_file_name)
xhtml_file_path = os.path.join(folder_path, xhtml_file_name)

print("********************************")
print("* Converting ASCIIDOC to XHTML *")
print("********************************")
print(f"Converting : {args.input_file} ==> {xhtml_file_path}")
subprocess.run(f"asciidoctor -b xhtml5 -a webfonts! {args.input_file} -o {xhtml_file_path}", shell=True)
print(f"-> Preparing : {xhtml_file_path}")

push_to_confluence(
    xhtml_file_path, 
    space=args.space, 
    parent_page_id=args.parent_page_id, 
    token=args.token
)
