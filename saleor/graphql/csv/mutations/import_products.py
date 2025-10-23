"""GraphQL mutation for importing products from CSV."""

import graphene
from django.core.exceptions import ValidationError

from ....csv.error_codes import ExportErrorCode
from ....csv.utils.product_import import import_products_from_csv
from ....permission.enums import ProductPermissions
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.mutations import BaseMutation
from ...core.types import BaseInputObjectType, ExportError, Upload


class ImportProductsInput(BaseInputObjectType):
    """Input fields for importing products from CSV."""

    file = Upload(
        required=True, description="CSV file containing product data to import."
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductImportResult(graphene.ObjectType):
    """Result of product import operation."""

    success = graphene.Boolean(
        description="Whether the import was successful.",
        required=True,
    )
    imported_count = graphene.Int(
        description="Number of products successfully imported.",
        required=True,
    )
    skipped_count = graphene.Int(
        description="Number of products skipped (already exist).",
        required=True,
    )
    error_count = graphene.Int(
        description="Number of errors encountered.",
        required=True,
    )
    errors = graphene.List(
        graphene.NonNull(lambda: ProductImportError),
        description="List of import errors.",
        required=True,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductImportError(graphene.ObjectType):
    """Error details for a failed product import."""

    row = graphene.Int(
        description="Row number in CSV file (1-based).",
        required=True,
    )
    slug = graphene.String(
        description="Product slug from the row.",
        required=True,
    )
    error = graphene.String(
        description="Error message.",
        required=True,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ImportProducts(BaseMutation):
    """Import products from a CSV file."""

    result = graphene.Field(
        ProductImportResult,
        description="Result of the import operation.",
    )

    class Arguments:
        input = ImportProductsInput(
            required=True, description="Fields required to import products from CSV."
        )

    class Meta:
        description = (
            "Import products from a CSV file. "
            "The CSV file must contain at least the following columns: "
            "slug, name, price. "
            "This mutation must be sent as a multipart request. "
            "More detailed specs of the upload format can be found here: "
            "https://github.com/jaydenseric/graphql-multipart-request-spec"
        )
        doc_category = DOC_CATEGORY_PRODUCTS
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ExportError
        error_type_field = "export_errors"

    @classmethod
    def validate_csv_file(cls, csv_file):
        """Validate the uploaded CSV file."""
        if not csv_file:
            raise ValidationError(
                {
                    "file": ValidationError(
                        "CSV file is required.",
                        code=ExportErrorCode.REQUIRED.value,
                    )
                }
            )

        # Check file extension
        file_name = csv_file.name.lower()
        if not file_name.endswith(".csv"):
            raise ValidationError(
                {
                    "file": ValidationError(
                        "File must be a CSV file (.csv extension).",
                        code=ExportErrorCode.INVALID.value,
                    )
                }
            )

        # Check file size (limit to 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if csv_file.size > max_size:
            raise ValidationError(
                {
                    "file": ValidationError(
                        f"File size exceeds maximum limit of {max_size / (1024 * 1024)}MB.",
                        code=ExportErrorCode.INVALID.value,
                    )
                }
            )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input
    ):
        """Execute the product import mutation."""
        csv_file = input.get("file")

        # Validate the CSV file
        cls.validate_csv_file(csv_file)

        # Read CSV content
        try:
            csv_content = csv_file.read().decode("utf-8")
        except UnicodeDecodeError:
            raise ValidationError(
                {
                    "file": ValidationError(
                        "CSV file must be UTF-8 encoded.",
                        code=ExportErrorCode.INVALID.value,
                    )
                }
            )

        # Import products
        import_result = import_products_from_csv(csv_content)

        # Convert errors to GraphQL format
        errors = [
            ProductImportError(
                row=error.get("row", 0),
                slug=error.get("slug", ""),
                error=error.get("error", "Unknown error"),
            )
            for error in import_result.get("errors", [])
        ]

        # Create result object
        result = ProductImportResult(
            success=import_result.get("success", False),
            imported_count=import_result.get("imported_count", 0),
            skipped_count=import_result.get("skipped_count", 0),
            error_count=import_result.get("error_count", 0),
            errors=errors,
        )

        return cls(result=result)
