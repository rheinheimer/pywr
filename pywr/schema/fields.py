from marshmallow import fields, ValidationError


# TODO this should be a parameter *reference*
class ParameterReferenceField(fields.Field):
    """ Marshmallow field representing a Parameter. """

    def _serialize(self, value, attr, obj):
        raise NotImplementedError('Serializing Parameters is not yet supported.')

    def _deserialize(self, value, attr, data):
        return value


# This is a parameter instance.
class ParameterField(fields.Field):
    """ Marshmallow field representing a Parameter. """
    def __init__(self, *args, **kwargs):
        self.wrap_constants = kwargs.pop('wrap_constants', False)
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj):
        raise NotImplementedError('Serializing Parameters is not yet supported.')

    def _deserialize(self, value, attr, data):
        model = self.context['model']
        from pywr.parameters import load_parameter, ConstantParameter
        param = load_parameter(model, value)

        if self.wrap_constants and isinstance(param, (int, float)):
            param = ConstantParameter(model, param)
        return param


class ParameterValuesField(fields.Field):
    """ Marshmallow field representing a ParameterValues. """

    def _serialize(self, value, attr, obj):
        raise NotImplementedError('Serializing Parameters is not yet supported.')

    def _deserialize(self, value, attr, data):
        model = self.context['model']
        klass = self.context.get('klass', None)
        obj = self.context.get('obj', None)

        # Try to coerce initial volume to float.
        try:
            return float(value)
        except TypeError:
            from pywr.parameters import load_parameter_values
            return load_parameter_values(model, value)

class NodeField(fields.Field):
    """ Marshmallow field representing a node. """
    def _serialize(self, value, attr, obj):
        raise NotImplementedError('Serializing Nodes is not yet supported.')

    def _deserialize(self, value, attr, data):
        model = self.context['model']
        klass = self.context.get('klass', None)
        obj = self.context.get('obj', None)

        return model._get_node_from_ref(model, value)


class ScenarioReferenceField(fields.Field):

    def _serialize(self, value, attr, obj):
        raise NotImplementedError('Serializing Scenario references is not yet supported.')

    def _deserialize(self, value, attr, data):
        model = self.context['model']
        klass = self.context.get('klass', None)
        obj = self.context.get('obj', None)

        return model.scenarios[value]


class PywrFloatField(fields.Float):

    def _serialize(self, value, attr, obj):
        raise NotADirectoryError('Serializing PywrFloatField is not yet supported.')

    def _deserialize(self, value, attr, data):

        try:
            ret = super()._deserialize(value, attr, data)
        except ValidationError:
            from pywr.parameters import load_parameter_values
            model = self.context['model']
            # TODO insert defaults column/index from attr/data['name'] respectively.
            ret = load_parameter_values(model, value)
            ret = super()._deserialize(ret, attr, data)

        return ret


class DataFrameField(fields.Field):

    def _deserialize(self, value, attr, data):

        from pywr.parameters import load_dataframe
        model = self.context['model']
        df = load_dataframe(model, value)
        return df


