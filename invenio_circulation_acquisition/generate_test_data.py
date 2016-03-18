def create_indices(app):
    from invenio_circulation_acquisition.models import entities
    from invenio_circulation_acquisition.mappings import mappings

    for name, _, cls in filter(lambda x: x[0] != 'Record', entities):
        mapping = mappings.get(name, {})
        index = cls.__tablename__
        cls._es.indices.delete(index=index, ignore=404)
        cls._es.indices.create(index=index, body=mapping)


def generate(app=None):
    import datetime

    import invenio_circulation_acquisition.models as models
    import invenio_circulation_acquisition.api as api

    create_indices(app)

    models.AcquisitionVendor.new(name='amazon.com', address='', email='',
                                 phone='', notes='')

    '''
    user = models.CirculationUser.get(1)
    record = models.CirculationRecord.get_all()[0]

    api.acquisition.request_acquisition(user, record)
    '''
