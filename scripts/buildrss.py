import argparse
import datetime
import glob
import operator
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
    parser.add_argument(
        '-p', '--pretty-print',
        help="pretty print XML",
        action='store_true',
        default=False,
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


def getpubdate(path: str) -> datetime.date:
    with open(path) as f:
        for line in f:
            if line.startswith('date:'):
                # 'date:', 'July', '5,', '2019'
                _, month, day, year = line.split()
                dt = datetime.datetime.strptime(line, 'date: %B %d, %Y\n')
                return dt.date()


def build_xml(sources):
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')

    ctitle = ET.SubElement(channel, 'title')
    ctitle.text = 'jchri.st rss'
    cdescription = ET.SubElement(channel, 'description')
    cdescription.text = 'ansible, python, erlang, and further ramblings'
    clink = ET.SubElement(channel, 'link')
    clink.text = 'https://jchri.st'

    for idx, (source, published) in enumerate(sources):
        if idx == 0:
            cpubdate = ET.SubElement(channel, 'pubDate')
            cpubdate.text = published.strftime('%a, %d %b %Y')

        item = ET.SubElement(channel, 'item')
        title = ET.SubElement(item, 'title')
        title.text = take_title(source)

        description = ET.SubElement(item, 'description')
        description.text = take_description(source)

        link = ET.SubElement(item, 'link')
        link.text = make_link(source)

        guid = ET.SubElement(item, 'guid')
        guid.text = link.text

        pubdate = ET.SubElement(item, 'pubDate')
        pubdate.text = published.strftime('%a, %d %b %Y')
    return rss


def main():
    args = get_parser().parse_args()
    files_by_date = ((path, getpubdate(path)) for path in glob.iglob(args.source_dir))
    sources = sorted(files_by_date, key=operator.itemgetter(1), reverse=True)

    with open(args.outfile, 'w+') as f:
        f.truncate()
        feed = build_xml(sources)
        if args.pretty_print:
            ET.indent(feed)
        f.write(ET.tostring(feed).decode())


if __name__ == '__main__':
    main()
