import pandas 
from tabulate import tabulate
from IPython.core.display import display, HTML


def display_question(candidate, wanted_attrs):
    """
    display properties of interest of one question
    
    :param classes.Question candidate: instance of class Question
    :param list wanted_attrs
    """
    list_of_lists = [[
        round(getattr(candidate, attr), 2) 
        if type(getattr(candidate, attr)) == float
        else getattr(candidate, attr)
        for attr in wanted_attrs
    ]]
    df = pandas.DataFrame(list_of_lists, columns=wanted_attrs)
    
    table = tabulate(df.transpose(), headers='keys', tablefmt='html')
    display(HTML(table))