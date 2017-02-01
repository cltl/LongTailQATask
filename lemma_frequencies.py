import glob
from collections import Counter


def create_iterable(root_folder, titles=False, content=False):
    """
    create iterable of .naf paths
    
    :param str root_folder: the root folder
    :param bool titles: include .title.naf files
    :param bool content: include .content.naf files
    
    :rtype: set
    :return: set .naf paths
    """
    nafs = set()
    
    for naf_path in glob.glob(root_folder + '/**/*.naf', recursive=True):
        if titles:
            title_path = json_path.replace('.json', '.title.naf')
            nafs.add(title_path)
        if content:
            content_path = json_path.replace('.json', '.content.naf')
            nafs.add(content_path)

    return nafs
    
root_folder = 'the_violent_corpus'
naf_paths = create_iterable(root_folder, titles=True, content=True)
print(len(naf_paths)
    
    
    
    
