from invenio_circulation.signals import (item_returned,
                                         circulation_other_actions)


def _item_returned(sender, data):
    import invenio_circulation_acquisition.models as models
    import invenio_circulation_acquisition.api as api

    item_id = data
    res = models.AcquisitionLoanCycle.search('item_id:{0}'.format(item_id))

    if res and len(res) == 1:
        api.acquisition.return_acquisition(res[0])
        return {'name': 'acquisition', 'result': True}

    return {'name': 'acquisition', 'result': None}


def _circulation_other_actions(sender, data):
    return {'name': 'acquisition',
            'priority': 0.75,
            'result': [('/circulation/acquisition/register_purchase/',
                        'Register Purchase'),
                       ('/circulation/acquisition/register_acquisition/',
                        'Register Acquisition')]}


item_returned.connect(_item_returned)
circulation_other_actions.connect(_circulation_other_actions)
