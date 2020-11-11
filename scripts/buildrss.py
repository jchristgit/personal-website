import argparse
import datetime
import glob
import operator
import os.path
import textwrap
import time
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


def getpubdate(path: str) -> datetime.datetime:
    with open(path) as f:
        for line in f:
            if line.startswith('date:'):
                # 'date:', 'July', '5,', '2019'
                _, month, day, year = line.split()
                return datetime.datetime.strptime(line, 'date: %B %d, %Y\n')


def build_xml(sources):
    rsstags = {'version': '2.0', 'xmlns:atom': "http://www.w3.org/2005/Atom"}
    rss = ET.Element('rss', **rsstags)
    channel = ET.SubElement(rss, 'channel')

    ctitle = ET.SubElement(channel, 'title')
    ctitle.text = 'jchri.st blog'
    cdescription = ET.SubElement(channel, 'description')
    cdescription.text = 'ansible, python, erlang, and further ramblings'
    clink = ET.SubElement(channel, 'link')
    clink.text = 'https://jchri.st'
    clastbuilddate = ET.SubElement(channel, 'lastBuildDate')
    clastbuilddate.text = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')
    catomlink = ET.SubElement(channel, 'atom:link', href='https://jchri.st/blog.rss', rel='self', type='application/rss+xml')

    for idx, (source, published) in enumerate(sources):
        lastmod = os.path.getmtime(source)
        as_time = time.localtime(lastmod)
        on_top = datetime.timedelta(hours=as_time.tm_hour, minutes=as_time.tm_min, seconds=as_time.tm_sec)
        published += on_top

        if idx == 0:
            cpubdate = ET.SubElement(channel, 'pubDate')
            cpubdate.text = published.strftime('%a, %d %b %Y %H:%M:%S +0200')

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
        pubdate.text = published.strftime('%a, %d %b %Y %H:%M:%S +0200')
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
