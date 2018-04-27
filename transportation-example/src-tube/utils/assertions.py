
"""
Dedicated to getting the results you intend from your graql queries
"""

# def check_insert_response(response, min_inserts_to_make=None, max_inserts_to_make=None):
#     """
#     Throws runtime errors the response doesn't show that the prescribed number of inserts were made
#     :param response:
#     :param min_inserts_to_make:
#     :param max_inserts_to_make:
#     :return:
#     """
#     if len(response) < min_inserts_to_make:
#         raise RuntimeError(("Grakn server response shows that {} insertions were made, but the minimum should have "
#                             "been {}. If using match, insert, check that the \"match\" on it's own returns at least "
#                             "one combination of variables.").format(len(response), min_inserts_to_make))
#     if len(response) > max_inserts_to_make:
#         raise RuntimeError(("Grakn server response shows that {} insertions were made, but the maximum should have "
#                             "been {}. If using match, insert, check that the \"match\" on it's own returns at the "
#                             "desired number of combinations of variables.").format(len(response), max_inserts_to_make))


def check_response_length(response, min_length=None, max_length=None):
    """
    Throws runtime errors the response doesn't show that the prescribed number of inserts were made
    :param response:
    :param min_length:
    :param max_length:
    :return:
    """
    if len(response) < min_length:
        raise RuntimeError(("Grakn server response has length {}, but the minimum should have been {}. If using match, "
                            "insert, check that the \"match\" on it's own returns at least one combination of variables"
                            ".").format(len(response), min_length))
    if len(response) > max_length:
        raise RuntimeError(("Grakn server response shows that {} insertions were made, but the maximum should have "
                            "been {}. If using match, insert, check that the \"match\" on it's own returns at the "
                            "desired number of combinations of variables.").format(len(response), max_length))