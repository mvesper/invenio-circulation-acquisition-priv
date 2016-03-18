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

class RequestedPurchase(BaseAcquisitions):
    current_status = models.AcquisitionLoanCycle.STATUS_REQUESTED
    acquisition_type = models.AcquisitionLoanCycle.TYPE_PURCHASE
    positive_actions = [('confirm_acquisition_request', 'CONFIRM',
                         'acquisition_vendor_price')]
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
