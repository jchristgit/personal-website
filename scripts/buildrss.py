import argparse
import glob
import os.path
import textwrap
from xml.etree import ElementTree as ET


def get_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '-s', '--source-dir',
        help="source file glob",
        default='content/blog/*.md'
    )
    parser.add_argument(
        '-o', '--outfile',
        help="where to write the RSS file",
        default='public/rss.xml'
    )
    return parser


def take_title(source):
    with open(source) as f:
        for line in f:
            if line.startswith('title: '):
                _, *title = line.split(maxsplit=1)
                return ' '.join(title)
    raise ValueError("cannot find title")


def take_description(source):
    header_tags = 0
    paragraph_tags = 0
    buf = []

    with open(source) as f:
        for line in f:
            header_tags += '---' in line
            paragraph_tags += header_tags and line == '\n'

            if paragraph_tags == 1:
                buf.append(line.strip())

            elif paragraph_tags == 2:
                return textwrap.shorten(
                    ' '.join(buf),
                    width=160
                )

    raise ValueError("cannot find description")


def make_link(path):
    return f'https://jchri.st/{path.replace(".md", ".html").replace("content/", "")}'


def build_xml(sources):
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')

    ctitle = ET.SubElement(channel, 'title')
    ctitle.text = 'jchri.st rss'
    cdescription = ET.SubElement(channel, 'description')
    cdescription.text = 'ansible erlang ...'
    clink = ET.SubElement(channel, 'link')
    clink.text = 'https://jchri.st'

    for source in sources:
        item = ET.SubElement(channel, 'item')
        title = ET.SubElement(item, 'title')
        title.text = take_title(source)

        description = ET.SubElement(item, 'description')
        description.text = take_description(source)

        link = ET.SubElement(item, 'link')
        link.text = make_link(source)

        guid = ET.SubElement(item, 'guid')
        guid.text = link.text
    return rss


def main():
    args = get_parser().parse_args()
    sources = sorted(glob.iglob(args.source_dir), key=os.path.getmtime, reverse=True)

    with open(args.outfile, 'w+') as f:
        f.truncate()
        feed = build_xml(sources)
        f.write(ET.tostring(feed).decode())


if __name__ == '__main__':
    main()