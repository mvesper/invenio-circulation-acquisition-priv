import invenio_circulation_acquisition.models as models

from flask import render_template


class BaseAcquisitions(object):
    positive_actions = None
    negative_actions = None

    @classmethod
    def entrance(cls):
        q = 'current_status:{0} acquisition_type:{1}'.format(
                cls.current_status, cls.acquisition_type)
        acquisition_lcs = models.AcquisitionLoanCycle.search(q)
        return render_template('lists/base_acquisitions.html',
                               acquisition_lcs=acquisition_lcs,
                               active_nav='lists',
                               positive_actions=cls.positive_actions,
                               negative_actions=cls.negative_actions)

    @classmethod
    def data(cls):
        q = 'current_status:{0} acquisition_type:{1}'.format(
                cls.current_status, cls.acquisition_type)
        return [{'id': x.id,
                 'item': cls._make(x),
                 'type': cls.type,
                 'positive_actions': cls.positive_actions,
                 'negative_actions': cls.negative_actions}
                for x in  models.AcquisitionLoanCycle.search(q)]

    @classmethod
    def _make(cls, loan_cycle):
        item = {}
        for name, accessor in zip(cls.table_header, cls.item_accessors):
            accessors = accessor.split('.')
            tmp = loan_cycle
            try:
                for access in accessors:
                    tmp = tmp.__getattribute__(access)
            except AttributeError:
                tmp = None
            item[name] = tmp

        return item


class RequestedPurchase(BaseAcquisitions):
    table_header = ['Borrower', 'CCID', 'Record']
    item_accessors = ['user.name', 'user.ccid', 'item.record.title']
    type = 'Purchase Request'
    current_status = models.AcquisitionLoanCycle.STATUS_REQUESTED
    acquisition_type = models.AcquisitionLoanCycle.TYPE_PURCHASE
    positive_actions = [('confirm_acquisition_request', 'CONFIRM',
                         'acquisition_confirmation')]
    negative_actions = [('cancel_acquisition_request', 'CANCEL')]


class OrderedPurchase(BaseAcquisitions):
    current_status = models.AcquisitionLoanCycle.STATUS_ORDERED
    acquisition_type = models.AcquisitionLoanCycle.TYPE_PURCHASE
    positive_actions = [('deliver_acquisition', 'DELIVER', None)]
    negative_actions = [('cancel_acquisition_request', 'CANCEL')]


class RequestedAcquisition(BaseAcquisitions):
    current_status = models.AcquisitionLoanCycle.STATUS_REQUESTED
    acquisition_type = models.AcquisitionLoanCycle.TYPE_ACQUISITION
    positive_actions = [('confirm_acquisition_request', 'CONFIRM',
                         'acquisition_vendor_price')]
    negative_actions = [('cancel_acquisition_request', 'CANCEL')]


class OrderedAcquisition(BaseAcquisitions):
    current_status = models.AcquisitionLoanCycle.STATUS_ORDERED
    acquisition_type = models.AcquisitionLoanCycle.TYPE_ACQUISITION
    positive_actions = [('deliver_acquisition', 'DELIVER', None)]
    negative_actions = [('cancel_acquisition_request', 'CANCEL')]
