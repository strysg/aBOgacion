"""
This is part of aBOgacion
Copyright Rodrigo Garcia 2026

Functions modified from gobbo-datos
"""

def get_selector_value(selector, *args):
    """Helps checking the selector value.
    Parameters:
    selector (str or function): If it is a function, uses args* to pass the function arguments and return
      a result. Else returns the selector string
    args (list): if `selector' is a function this args are passed as arguments to that function
    Returns:
    str: Resulting selector
    """
    svalue = ''
    if isinstance(selector['value'], str) is False:
        svalue = selector['value'](*args)
    else:
        svalue = selector['value']
    return svalue


def get_locator(selector, *args):
    """Replaces the selector values and returns a valid string to be used in
    playright page.locator"""

    svalue = get_selector_value(selector, *args)
    if selector['stype'] == 'xpath':
        svalue = f'xpath={svalue}'
    if selector['stype'] == 'css':
        svalue = f'css={svalue}'
    return svalue


async def is_element_located(page, selector, *args):
    """Tries to get the element from the given selector on the given page obeject.
    If element is not located or visible returns False
    """
    element = page.locator(get_locator(selector, *args))
    if await element.count() > 0:
        return True
    return False

    
async def get_text_from_all_elements(self, locator, *args):
    """Gets the text from all elements that matches the locator.
       When there are multiple elements the text is concat with ,
        If no element is found returns an empty string
    """
    text = ''
    if await is_element_located(self.page, locator):
        web_elements =  await self.page.locator(get_locator(locator, *args)).all()
        if len(web_elements) == 1:
            return await web_elements[0].inner_text()
        
        for web_element in web_elements:
            text += await web_element.inner_text() + ','
    return text


async def get_all_elements_from_locator(page, selector, throw_exception=True, *args):
    """Returns all the elements for the given page and locator

    Parameters:
    page (Page Object playwrigth): Page object from browser context to search in
    locator: locator string
    throw_exception (bool): If true, raises an exception when no element for the given
      locator is found, otherwise will return an empty list
    args (Arg list): Additional args list for the selector

    Returns:
    List of Web elements found
    """
    try:
        return await page.locator(get_locator(selector, *args)).all()
    except Exception as e:
        if not throw_exception:
            LOGGER.warn(f'Not able to get elements with selector {selector}')
            return []
        LOGGER.error(f'Error getting elements with selector {selector}')
        LOGGER.error(LOGGER.format_exception(e))
        raise e



def get_selector_value(selector, *args):
    """Helps checking the selector value.
    Parameters:
    selector (str or function): If it is a function, uses args* to pass the function arguments and return
      a result. Else returns the selector string
    args (list): if `selector' is a function this args are passed as arguments to that function
    Returns:
    str: Resulting selector
    """
    svalue = ''
    if isinstance(selector['value'], str) is False:
        svalue = selector['value'](*args)
    else:
        svalue = selector['value']
    return svalue


def get_locator(selector, *args):
    """Replaces the selector values and returns a valid string to be used in
    playright page.locator"""

    svalue = get_selector_value(selector, *args)
    if selector['stype'] == 'xpath':
        svalue = f'xpath={svalue}'
    if selector['stype'] == 'css':
        svalue = f'css={svalue}'
    LOGGER.debug(f'  locator: {svalue}')
    return svalue
