# Copyright (c) 2018, Novo Nordisk Foundation Center for Biosustainability,
# Technical University of Denmark.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Marshmallow schemas for marshalling the API endpoints."""

from marshmallow import Schema, fields


class StrictSchema(Schema):
    """Shared empty schema instance with strict validation."""

    class Meta:
        """Meta class for marshmallow schemas."""

        strict = True


class DesignSchema(StrictSchema):
    # See the Caffeine frontend for data schemas for the below fields. Consider
    # adding the schema constraints here as well.
    reaction_knockins = fields.List(fields.Raw(required=True))
    reaction_knockouts = fields.List(fields.Raw(required=True))
    gene_knockouts = fields.List(fields.Raw(required=True))
    constraints = fields.List(fields.Raw(required=True))


class DesignBaseSchema(StrictSchema):
    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    name = fields.Str(required=True)
    model_id = fields.Integer(required=True)
    design = fields.Nested(DesignSchema, required=True)
    method = fields.Str(required=True)
