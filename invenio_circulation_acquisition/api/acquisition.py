import datetime

from invenio_circulation.api.item import create as create_item
from invenio_circulation.api.event import create as create_event
from invenio_circulation.api.utils import email_notification
from invenio_circulation.api.utils import ValidationExceptions

from invenio_circulation.models import CirculationItem
from invenio_circulation_acquisition.models import AcquisitionLoanCycle


def _create_acquisition_temporary_item(record):
    acquisition_tmp = 'acquisition_temporary_no_value'
    status = CirculationItem.STATUS_ON_SHELF
    group = CirculationItem.GROUP_BOOK
    item = create_item(record.id, 1, acquisition_tmp, acquisition_tmp,
                       acquisition_tmp, acquisition_tmp,
                       acquisition_tmp, acquisition_tmp, status, group)
    item.additional_statuses.append('acquisition_temporary')
    item.save()

    return item


def request_acquisition(user, record, acquisition_type, copies,
                        payment_method, budget_code='', price='',
                        delivery=None, comments=''):
    if not delivery:
        delivery = AcquisitionLoanCycle.DELIVERY_DEFAULT

    item = _create_acquisition_temporary_item(record)

    acquisition_clc = AcquisitionLoanCycle.new(
            current_status=AcquisitionLoanCycle.STATUS_REQUESTED,
            item=item, user=user,
            acquisition_type=acquisition_type,
            copies=copies,
            payment_method=payment_method,
            budget_code=budget_code,
            price=price,
            delivery=delivery,
            comments=comments,
            issued_date=datetime.datetime.now())

    if acquisition_type == 'acquisition':
        event = AcquisitionLoanCycle.EVENT_ACQUISITION_REQUEST
    elif acquisition_type == 'purchase':
        event = AcquisitionLoanCycle.EVENT_PURCHASE_REQUEST

    create_event(user_id=user.id, item_id=item.id,
                 acquisition_loan_cycle_id=acquisition_clc.id,
                 event=event)

    email_notification('acquisition_request', 'john.doe@cern.ch', user.email,
                       name=user.name, action='requested', items=item)

    return acquisition_clc


def try_confirm_acquisition_request(acquisition_loan_cycle):
    exceptions = []
    try:
        status = AcquisitionLoanCycle.STATUS_REQUESTED
        assert (acquisition_loan_cycle.current_status == status,
                'The acquisition loan cycle is in the wrong state')
    except AssertionError as e:
        exceptions.append(('acquisition', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def confirm_acquisition_request(acquisition_loan_cycle,
                                vendor_id, price, currency, comments):
    try:
        try_confirm_acquisition_request(acquisition_loan_cycle)
    except ValidationExceptions as e:
        raise e

    acquisition_loan_cycle.current_status = AcquisitionLoanCycle.STATUS_ORDERED
    acquisition_loan_cycle.vendor_id = vendor_id
    acquisition_loan_cycle.price = price
    acquisition_loan_cycle.currency = currency
    acquisition_loan_cycle.comments = comments
    acquisition_loan_cycle.save()

    create_event(acquisition_loan_cycle_id=acquisition_loan_cycle.id,
                 event=AcquisitionLoanCycle.EVENT_ACQUISITION_ORDERED)

    email_notification('acquisition_ordered', 'john.doe@cern.ch',
                       acquisition_loan_cycle.user.email,
                       acquisition_loan_cycle=acquisition_loan_cycle)


def try_receive_acquisition(acquisition_loan_cycle):
    exceptions = []
    try:
        status = AcquisitionLoanCycle.STATUS_ORDERED
        assert (acquisition_loan_cycle.current_status == status,
                'The acquisition loan cycle is in the wrong state')
    except AssertionError as e:
        exceptions.append(('acquisition', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def receive_acquisition(acquisition_loan_cycle):
    try:
        try_receive_acquisition(acquisition_loan_cycle)
    except ValidationExceptions as e:
        raise e

    status = AcquisitionLoanCycle.STATUS_RECEIVED
    acquisition_loan_cycle.current_status = status
    acquisition_loan_cycle.save()

    create_event(acquisition_loan_cycle_id=acquisition_loan_cycle.id,
                 event=AcquisitionLoanCycle.EVENT_ACQUISITION_RECEIVED)

    email_notification('acquisition_ordered', 'john.doe@cern.ch',
                       acquisition_loan_cycle.user.email,
                       acquisition_loan_cycle=acquisition_loan_cycle)


def try_cancel_acquisition_request(acquisition_loan_cycle):
    exceptions = []
    try:
        status1 = AcquisitionLoanCycle.STATUS_REQUESTED
        status2 = AcquisitionLoanCycle.STATUS_ORDERED
        assert (acquisition_loan_cycle.current_status == status1 or
                acquisition_loan_cycle.current_status == status2,
                'The acquisition loan cycle is in the wrong state')
    except AssertionError as e:
        exceptions.append(('acquisition', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def cancel_acquisition_request(acquisition_loan_cycle, reason=''):
    try:
        try_cancel_acquisition_request(acquisition_loan_cycle)
    except ValidationExceptions as e:
        raise e

    status = AcquisitionLoanCycle.STATUS_CANCELED
    acquisition_loan_cycle.current_status = status
    acquisition_loan_cycle.save()

    create_event(acquisition_loan_cycle_id=acquisition_loan_cycle.id,
                 event=AcquisitionLoanCycle.EVENT_ACQUISITION_CANCELED,
                 description=reason)


def try_decline_acquisition_request(acquisition_loan_cycle):
    exceptions = []
    try:
        status = AcquisitionLoanCycle.STATUS_REQUESTED
        assert (acquisition_loan_cycle.current_status == status,
                'The acquisition loan cycle is in the wrong state')
    except AssertionError as e:
        exceptions.append(('acquisition', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def decline_acquisition_request(acquisition_loan_cycle):
    try:
        try_decline_acquisition_request(acquisition_loan_cycle)
    except ValidationExceptions as e:
        raise e

    status = AcquisitionLoanCycle.STATUS_DECLINED
    acquisition_loan_cycle.current_status = status
    acquisition_loan_cycle.save()

    create_event(acquisition_loan_cycle_id=acquisition_loan_cycle.id,
                 event=AcquisitionLoanCycle.EVENT_ACQUISITION_DECLINED)

    email_notification('acquisition_declined', 'john.doe@cern.ch',
                       acquisition_loan_cycle.user.email,
                       acquisition_loan_cycle=acquisition_loan_cycle)


def try_deliver_acquisition(acquisition_loan_cycle):
    exceptions = []
    try:
        status = AcquisitionLoanCycle.STATUS_ORDERED
        assert (acquisition_loan_cycle.current_status == status,
                'The acquisition loan cycle is in the wrong state')
    except AssertionError as e:
        exceptions.append(('acquisition', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def deliver_acquisition(acquisition_loan_cycle):
    try:
        try_deliver_acquisition(acquisition_loan_cycle)
    except ValidationExceptions as e:
        raise e

    status = AcquisitionLoanCycle.STATUS_DELIVERED
    acquisition_loan_cycle.current_status = status
    acquisition_loan_cycle.save()

    create_event(acquisition_loan_cycle_id=acquisition_loan_cycle.id,
                 event=AcquisitionLoanCycle.EVENT_ACQUISITION_DELIVERED)

    email_notification('acquisition_delivery', 'john.doe@cern.ch',
                       acquisition_loan_cycle.user.email,
                       acquisition_loan_cycle=acquisition_loan_cycle)
