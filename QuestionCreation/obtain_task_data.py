from newspaper import Article
import hashlib
import json
import time
from datetime import datetime

def download_article(url):
    """
    download article and return title + body

    :param str url: url to news article

    :rtype: tuple
    :return: (title, title_checksum, body, body_checksum)
    """

    a = Article(url, language='en')
    a.download()
    attempts = 0
    max_sec = 10

    while not a.is_downloaded:
        time.sleep(1)
        attempts += 1

        if attempts == max_sec:
            print("Extraction error with the article %s" % url)
            return (None, None, None, None)

    a.parse()
    title = a.title
    content = a.text

    hash_obj = hashlib.md5(title.encode())
    title_hash = hash_obj.hexdigest()

    hash_obj = hashlib.md5(content.encode())
    content_hash = hash_obj.hexdigest()

    return (title, title_hash, content, content_hash)


def pre_tokenization_to_conll(tokenization_path,
                              output_path,
                              text):
    """
    """
    with open(output_path, 'w') as outfile:
        with open(tokenization_path) as infile:
            for line in infile:
                id_, offset, length = line.strip().split('\t')

                offset = int(offset)
                length = int(length)

                token = text[offset: offset + length]
                token = token.replace('\n', '-')

                info = [id_, token]

                outfile.write('\t'.join(info) + '\n')


input_folder = 'trial'
path_doc_id2article_url = 'pre/doc_id2article_url.json'.format_map(locals())
doc_id2article_url = json.load(open(path_doc_id2article_url))

title_succes = 0
title_failed = 0
body_succes = 0
body_failed = 0

maximum = 50
counter = 0

print('start', datetime.now())

for doc_id, article_url in doc_id2article_url.items():

    counter += 1
    if counter >= maximum:
        break

    if counter % 1 == 0:
        print(counter)

    # load checksums
    checksum_path = 'pre/{doc_id}.checksum.conll'.format_map(locals())
    checksums = json.load(open(checksum_path))

    # scrape article
    title, title_hash, content, content_hash = download_article(article_url)
    if title is None:
        title_failed += 1
        body_failed += 1
        continue

    # check checksums
    if checksums['title'] == title_hash:

        # reconstruct title.conll
        pre_title_conll = 'pre/{doc_id}.title.conll'.format_map(locals())
        post_title_conll = 'post/{doc_id}.title.conll'.format_map(locals())

        pre_tokenization_to_conll(pre_title_conll, post_title_conll, title)

        title_succes += 1

    else:
        print('CHECKSUM for title of {doc_id} failed: {article_url}'.format_map(locals()))
        title_failed += 1

    if checksums['body'] == content_hash:
        # reconstruct body.conll
        pre_body_conll = 'pre/{doc_id}.body.conll'.format_map(locals())
        post_body_conll = 'post/{doc_id}.body.conll'.format_map(locals())
        pre_tokenization_to_conll(pre_body_conll, post_body_conll, content)

        body_succes += 1

    else:
        print('CHECKSUM for body of {doc_id} failed: {article_url}'.format_map(locals()))
        body_failed += 1

print('body failed', body_failed)
print('body succes', body_succes)
print('title failed', title_failed)
print('title succes', title_succes)

print('end', datetime.now())

