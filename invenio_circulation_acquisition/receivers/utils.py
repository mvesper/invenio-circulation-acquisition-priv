from invenio_circulation.signals import (
        circ_apis, run_action, try_action, convert_params)


def _get_action(action, try_action=False):
    import invenio_circulation_acquisition.api as api

    actions = {'confirm_acquisition_request': (api.acquisition,
                                               'confirm_acquisition_request'),
               'receive_acquisition': (api.acquisition, 'receive_acquisition'),
               'deliver_acquisition': (api.acquisition, 'deliver_acquisition'),
               'decline_acquisition_request': (api.acquisition,
                                               'decline_acquisition_request'),
               'cancel_acquisition_request': (api.acquisition,
                                              'cancel_acquisition_request'),
               'request_acquisition_extension':
               (api.acquisition, 'request_acquisition_extension'),
               'lose_acquisition': (api.acquisition, 'lose_acquisition')}

    try_action = 'try_' if try_action else ''

    _api, func_name = actions[action]

    return getattr(_api, try_action + func_name)


def _try_action(action, data):
    from invenio_circulation.api.utils import ValidationExceptions
    from invenio_circulation.views.utils import filter_params

    try:
        filter_params(_get_action(action, True), **data)
        res = True
    except KeyError:
        res = None
    except ValidationExceptions as e:
        res = [(ex[0], str(ex[1])) for ex in e.exceptions]

    return {'name': 'acquisition', 'result': res}


def _run_action(action, data):
    from invenio_circulation.views.utils import filter_params

    try:
        filter_params(_get_action(action), **data)
        res = _get_message(action, data)
    except KeyError:
        res = None

    return {'name': 'acquisition', 'result': res}


def _get_message(action, data):
    return 'success'


def _apis(entity, data):
    import invenio_circulation_acquisition.api as api

    apis = {'acquisition_loan_cycle': api.acquisition}

    return {'name': 'acquisition', 'result': apis.get(entity)}


def _convert_params(entity, data):
    import invenio_circulation_acquisition.models as models

    try:
        acquisition_lc_id = data['acquisition_lc_id']
        acquisition_lc = models.AcquisitionLoanCycle.get(acquisition_lc_id)
    except Exception:
        acquisition_lc = None

    res = {'acquisition_loan_cycle': acquisition_lc}

    return {'name': 'acquisition', 'result': res}


circ_apis.connect(_apis)
try_action.connect(_try_action)
run_action.connect(_run_action)
convert_params.connect(_convert_params)
