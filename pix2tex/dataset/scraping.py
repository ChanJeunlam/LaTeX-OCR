import os
import sys
import random
from tqdm import tqdm
import html
import requests
import re
from typing import Callable, List, Tuple
from pix2tex.dataset.extract_latex import find_math

wikilinks = re.compile(r'href="/wiki/(.*?)"')
htmltags = re.compile(r'<(noscript|script)>.*?<\/\1>', re.S)
wiki_base = 'https://en.wikipedia.org/wiki/'


def parse_url(url, encoding=None):
    r = requests.get(url)
    if r.ok:
        if encoding:
            r.encoding = encoding
        return html.unescape(re.sub(htmltags, '', r.text))


def parse_wiki(url):
    text = parse_url(url)
    linked = list(set([l for l in re.findall(wikilinks, text) if not ':' in l]))
    return find_math(text, wiki=True), linked


# recursive search
def recursive_search(parser: Callable,  seeds: List[str], depth: int = 2, skip: List[str] = [], unit: str = 'links', base_url: str = None, **kwargs) -> Tuple[List[str], List[str]]:
    """Find math recursively. Look in `seeds` for math and further sites to look.

    Args:
        parser (Callable): A function that returns a `Tuple[List[str], List[str]]` of math and ids (for `base_url`) respectively.
        seeds (List[str]): Fist set of ids.
        depth (int, optional): How many iterations to look for. Defaults to 2.
        skip (List[str], optional): List of alreadly visited ids. Defaults to [].
        unit (str, optional): Tqdm verbose unit description. Defaults to 'links'.
        base_url (str, optional): Base url to add ids to. Defaults to None.

    Returns:
        Tuple[List[str],List[str]]: Returns list of found math and visited ids respectively.
    """
    visited, links = set(skip), set(seeds)
    math = []
    try:
        for i in range(int(depth)):
            link_list = list(links)
            random.shuffle(link_list)
            t_bar = tqdm(link_list, initial=len(visited), unit=unit)
            for link in t_bar:
                if not link in visited:
                    t_bar.set_description('searching %s' % (link))
                    if base_url:
                        m, l = parser(base_url+link, **kwargs)
                    else:
                        m, l = parser(link, **kwargs)
                    # check if we got any math from this wiki page and
                    # if not terminate the tree
                    if len(m) > 0:
                        for li in l:
                            links.add(li)
                        t_bar.total = len(links)
                        math.extend(m)
                    visited.add(link)
        return list(visited), list(set(math))
    except Exception as e:
        raise(e)
        return list(visited), list(set(math))
    except KeyboardInterrupt:
        return list(visited), list(set(math))

# recursive wiki search


def recursive_wiki(seeds, depth=4, skip=[]):
    '''Recursivley search wikipedia for math. Every link on the starting page `start` will be visited in the next round and so on, until there is no 
    math in the child page anymore. This will be repeated `depth` times.'''
    start = [s.split('/')[-1] for s in seeds]
    return recursive_search(parse_wiki, start, depth, skip, base_url=wiki_base, unit='links')


if __name__ == '__main__':
    if len(sys.argv) > 2:
        url = [sys.argv[1]]
    else:
        url = ['https://en.wikipedia.org/wiki/Mathematics', 'https://en.wikipedia.org/wiki/Physics']
    try:
        visited, math = recursive_wiki(url)
    except KeyboardInterrupt:
        pass
    for l, name in zip([visited, math], ['visited_wiki.txt', 'math_wiki.txt']):
        f = open(os.path.join(sys.path[0], 'data', name), 'a', encoding='utf-8')
        for element in l:
            f.write(element)
            f.write('\n')
        f.close()
