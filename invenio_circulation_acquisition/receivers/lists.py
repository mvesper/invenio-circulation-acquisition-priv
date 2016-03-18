from invenio_circulation.signals import (lists_overview,
                                                 lists_class)


def _lists_overview(sender, data):
    return {'name': 'acquisition_lists',
            'priority': 1.0,
            'result': [('Purchase Requests', 'requested_purchase'),
                       ('Ordered Purchase Requests', 'ordered_purchase'),
                       ('Acquisition Requests', 'requested_acquisition'),
                       ('Ordered Acquisition Requests',
                        'ordered_acquisition')]}


def _lists_class(link, data):
    from invenio_circulation_acquisition.lists.acquisition import *

    clazzes = {'requested_acquisition': RequestedAcquisition,
               'ordered_acquisition': OrderedAcquisition,
               'requested_purchase': RequestedPurchase,
               'ordered_purchase': OrderedPurchase}

    return {'name': 'acquisition_lists', 'result': clazzes.get(link)}

lists_overview.connect(_lists_overview)
lists_class.connect(_lists_class)
