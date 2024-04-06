# A script to parse Kindle highlights into Markdown.
# Free alternative to Clippings and Readwise.
# Requires Python 3.10 or higher.

import re
import argparse
from pathlib import Path
from enum import Enum
from collections import defaultdict
from typing import Dict, List, Tuple


HIGHLIGHT_SEPARATOR = (
    "=========="  # The separator between highlights in the My Clippings.txt file.
)
FILE_NAME = "My Clippings.txt"  # The file name of the Kindle highlights file.
SAVE_PATH = "books/"  # Where to save the markdown files. The default is a folder named 'books' in the current directory.


class Highlight:
    def __init__(self, raw_string: str):
        (
            self.title,
            self.author,
            self.content,
            self.date,
            self.page,
        ) = Highlight.parse_single_highlight(raw_string)

    def __str__(self):
        return f"<Highlight Object> Title:{self.title}\tAuthor:{self.author}\tContent:{self.content}\tDate:{self.date}\tPage:{self.page}"

    @staticmethod
    def parse_single_highlight(highlight_string: str) -> Tuple[str, str, str, str, str]:
        """Parse a single highlight string and return its components.

        This static method takes a single highlight string, which represents a highlight
        from a Kindle highlights file, and parses it into its individual components.

        Args:
            highlight_string (str): The raw highlight string to be parsed.

        Returns:
            Tuple[str, str, str, str, str]: A tuple containing the following elements:
                1. The book name
                2. The highlight text
                3. The location (e.g., location number)
                4. The date of the highlight (if `add_date` is `True`)
                5. The page number (if `add_page` is `True`)
            Will be all empty strings if the highlight string is not in the expected format.
        """
        split_string = list(filter(None, highlight_string.split("\n")))

        if len(split_string) != 3:
            return "", "", "", "", ""
            # return None, None, None, None, None

        # first parse
        author_line = split_string[0]
        content = split_string[-1]
        details = split_string[-2].split("|")

        # parse author and title
        regex = r"\((.*?)\)"
        match = re.search(regex, author_line)

        if not match:
            return "", "", "", "", ""
            # return None, None, None, None, None

        author = match.group(1)
        title = author_line[: match.start()]

        # Parse additional info
        date = details[-1][10:]
        page_idx = details[0].strip().find("page")
        page = "P" + details[0][page_idx + 1 : -1]

        return title, author, content, page, date


class Formatting(Enum):
    """Represents the different output formats for the highlights.
    Options are:
    - BULLET: Bullet points
    - QUOTE: Block quotes
    - PARAGRAPH: Plain text paragraphs
    """

    # If you want to implement more formatting options, add them here.
    # Then, update the `format_highlight` method to handle the new option.
    BULLET = "bullet"
    QUOTE = "quote"
    PARAGRAPH = "paragraph"

    def __str__(self):
        return self.value

    def format_highlight(
        self, highlight: Highlight, add_date=True, add_page=True
    ) -> str:
        """Format a highlight based on the selected formatting option.

        Args:
            highlight (str): The highlight text to be formatted.
            add_date (bool, optional): Whether to add the date the highlight was made. Defaults to `True`.
            add_page (bool, optional): Whether to add the page number of the highlight. Defaults to `True`.

        Returns:
            str: The formatted highlight text.
        """
        formatted_text = highlight.content.replace("\n", " ")

        match self:
            case Formatting.QUOTE:
                formatted_text = f"- {formatted_text}"
            case Formatting.BULLET:
                formatted_text = f"> {formatted_text}"
            case Formatting.PARAGRAPH:
                formatted_text = f"{formatted_text}"
            case _:
                raise ValueError(f"Invalid formatting option: {self.value}")

        if add_date and add_page:
            formatted_text = (
                f"{formatted_text} (Added on {highlight.date}, {highlight.page})"
            )
        elif add_date and not add_page:
            formatted_text = f"{formatted_text} (Added on {highlight.date})"
        elif not add_date and add_page:
            formatted_text = f"{formatted_text} ({highlight.page})"
        return formatted_text + "\n"


class Parser:
    """Parses the Kindle highlights file."""

    def __init__(self):
        self.books: Dict[Tuple[str, str], List[Highlight]] = defaultdict(list)

    def parse_highlights(self, file_name=FILE_NAME):
        """This method reads the contents of the provided Kindle highlights file, parses the data, and and stores the resulting `Highlight` objects in the `self.books` attribute of the class.

        Args:
            file_name (str, optional): The path to the Kindle highlights file. Defaults to `FILE_NAME`.
        """
        with open(file_name, "r") as file:
            data = file.read()
        highlights = data.split(HIGHLIGHT_SEPARATOR)
        for raw_string in highlights:
            h = Highlight(raw_string)
            if h.title and h.author:
                self.books[(h.author, h.title)].append(h)

    def write_highlights(
        self,
        save_path=SAVE_PATH,
        formatting=Formatting.BULLET,
        add_date=True,
        add_page=True,
        overwrite=False,
    ):
        """Write the parsed highlights to markdown files. Creates the folder `save_path` if it doesn't exist.

        Args:
            save_path (str, optional): The path to save the markdown files. Defaults to `SAVE_PATH`.
            formatting (Formatting, optional): The output format for the highlights. Defaults to `Formatting.BULLET`.
            add_date (bool, optional): Whether to add the date the highlight was made. Defaults to `True`.
            add_page (bool, optional): Whether to add the page number of the highlight. Defaults to `True`.
            overwrite (bool, optional): Whether to overwrite existing files. Defaults to `False`.
        """
        # Create the directory if it doesn't exist
        Path(save_path).mkdir(exist_ok=True)

        # Write each book's highlights to a markdown file
        for (author, title), highlights in self.books.items():
            clean_title = "".join(
                [c for c in title if c.isalpha() or c.isdigit() or c == " "]
            ).rstrip()
            clean_author = "".join(
                [c for c in author if c.isalpha() or c.isdigit() or c == " "]
            ).rstrip()
            if (
                not overwrite
                and Path(f"{save_path}{clean_author}_{clean_title}.md").exists()
            ):
                print(
                    f"- Skipping {clean_author}_{clean_title}.md as it already exists."
                )
                continue
            with open(f"{save_path}{clean_author}_{clean_title}.md", "w") as file:
                file.write(f"# {clean_title}\n")
                file.write("\n")
                file.write(f"Author: {clean_author}\n")
                file.write("\n")
                for h in highlights:
                    formatted_text = formatting.format_highlight(h, add_date, add_page)
                    file.write(formatted_text)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description=f"Parse Kindle highlights into markdown. Reads highlights from '{FILE_NAME}' and saves each book as a Markdown file to '{SAVE_PATH}'."
    )
    arg_parser.add_argument(
        "-f",
        "--format",
        type=Formatting,
        choices=list(Formatting),
        default=Formatting.BULLET,
        help=f"The output format for the highlights. Defaults to {Formatting.BULLET}.",
    )
    arg_parser.add_argument(
        "--save_path",
        type=str,
        default=SAVE_PATH,
        help=f"The path to save the markdown files. Defaults to {SAVE_PATH}.",
    )
    arg_parser.add_argument(
        "-d",
        "--date",
        action="store_true",
        help="Add the date the highlight was made to the output.",
    )
    arg_parser.add_argument(
        "-p",
        "--page",
        action="store_true",
        help="Add the page number of the highlight to the output.",
    )
    arg_parser.add_argument(
        "-o",
        "--overwrite",
        action="store_true",
        help="Overwrite existing files.",
    )

    args = arg_parser.parse_args()

    parser = Parser()
    print(f"\U0001f50d Parsing highlights in {FILE_NAME}...")
    parser.parse_highlights()
    print("\n\U0001f4c1 Creating markdown files...")
    parser.write_highlights(
        args.save_path, args.format, args.date, args.page, args.overwrite
    )
    print(
        f"\n\U0001f680 Done! You can find the markdown files in the '{args.save_path}' directory."
    )
