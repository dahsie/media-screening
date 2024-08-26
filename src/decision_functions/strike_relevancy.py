def strike_relevancy(item: dict, args : dict) -> bool:
    """
    Determines the relevancy of an article related to a labor strike based on specific criteria.

    Args:
    -----
    item : dict
        A dictionary containing details of an article.
    args : dict
        A dictionary containing parameters to evaluate relevancy, including 'sectors_to_discard' and 'desirable_temporalities'.

    Returns:
    --------
    bool
        True if the article meets all relevancy criteria, False otherwise.
    """
    
    liste = set([sector.lower() for sector in item['impacted_business_sectors']])
    sectors_to_discard = set(args['sectors_to_discard'])
    
    is_sector_relevant = len(liste.intersection(sectors_to_discard)) == 0
    is_event_nature_qualified = item['strike']['labor_strike'] == 'yes'
    is_company_impacted = item['impacted_company'] != ''
    is_automotive_concerned = item['automotive_industry']['concerned'].lower() == "yes"
    is_supplier_yes = item['supplier'].lower() == "yes"
    is_temorality_relevant = item['temporality']['strike_status'] in args['desirable_temporalities']

    if (is_sector_relevant and is_event_nature_qualified and is_company_impacted and is_automotive_concerned and is_supplier_yes and is_temorality_relevant):
        return True
    return False