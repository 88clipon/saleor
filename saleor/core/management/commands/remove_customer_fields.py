from django.core.management.base import BaseCommand
from saleor.attribute.models import Attribute, AttributeVariant, AttributeProduct


class Command(BaseCommand):
    help = "Remove Brand Name and Model and Frame Size attributes from product types"

    def handle(self, *args, **options):
        """Remove customer-provided fields from admin dashboard."""

        # Find the attributes by name (they might have different slugs)
        attributes_to_remove = []

        # Search for attributes with names containing these keywords
        for attr in Attribute.objects.all():
            name_lower = attr.name.lower()
            if "brand" in name_lower and "model" in name_lower:
                attributes_to_remove.append(attr)
                self.stdout.write(
                    f"Found Brand/Model attribute: {attr.name} (slug: {attr.slug})"
                )
            elif "frame" in name_lower and "size" in name_lower:
                attributes_to_remove.append(attr)
                self.stdout.write(
                    f"Found Frame Size attribute: {attr.name} (slug: {attr.slug})"
                )

        if not attributes_to_remove:
            self.stdout.write(
                self.style.WARNING(
                    "No Brand Name and Model or Frame Size attributes found."
                )
            )
            return

        # Remove these attributes from all product types
        for attr in attributes_to_remove:
            self.stdout.write(
                f"\nRemoving attribute '{attr.name}' from all product types..."
            )

            # Remove from variant attributes (this is what shows in the dashboard)
            variant_assignments = AttributeVariant.objects.filter(attribute=attr)
            count = variant_assignments.count()
            if count > 0:
                self.stdout.write(
                    f"  - Removing from {count} product type variant assignments"
                )
                variant_assignments.delete()

            # Also remove from product attributes if they exist
            product_assignments = AttributeProduct.objects.filter(attribute=attr)
            count = product_assignments.count()
            if count > 0:
                self.stdout.write(
                    f"  - Removing from {count} product type product assignments"
                )
                product_assignments.delete()

            self.stdout.write(
                f"  - Attribute '{attr.name}' removed from all product types"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Successfully removed {len(attributes_to_remove)} customer field attributes from product types.\n"
                "These fields will no longer appear in the admin dashboard for product/variant editing.\n"
                "They will still be captured as customer input during checkout."
            )
        )
