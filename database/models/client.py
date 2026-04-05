"""
Client Dimension Model
Represents client master data: demographics, onboarding, AUM, relationship manager
"""
from django.db import models


class ClientDim(models.Model):
    """
    Client master dimension table.
    One record per unique client ID/PAN.
    """
    
    # Identifiers
    client_id_pan = models.CharField(max_length=50, unique=True, db_index=True, 
                                      help_text="Client ID or PAN number")
    client_name = models.CharField(max_length=255, db_index=True)
    group_code = models.CharField(max_length=50, null=True, blank=True, db_index=True,
                                   help_text="Group/branch code for the client")
    
    # Account details
    onboarded_date = models.DateField(null=True, blank=True, db_index=True,
                                       help_text="Date client was onboarded")
    aum = models.CharField(max_length=50, null=True, blank=True,
                           help_text="Assets Under Management (stored as string, e.g., '3.29 Cr')")
    
    # Relationship manager
    relationship_manager = models.CharField(max_length=255, null=True, blank=True, db_index=True,
                                            help_text="Name of the assigned relationship manager")
    rm_pan = models.CharField(max_length=50, null=True, blank=True,
                              help_text="PAN of the relationship manager")
    
    # Metadata
    source_file = models.CharField(max_length=255, null=True, blank=True, 
                                   help_text="Excel filename this record was loaded from")
    loaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    row_hash = models.CharField(max_length=64, null=True, blank=True, unique=True, db_index=True,
                                help_text="SHA256 hash of row for duplicate detection")
    
    class Meta:
        db_table = 'client_dim'
        indexes = [
            models.Index(fields=['client_name']),
            models.Index(fields=['relationship_manager']),
        ]
        verbose_name = 'Client Dimension'
        verbose_name_plural = 'Client Dimensions'
        ordering = ['client_name']
    
    def __str__(self):
        return f"{self.client_id_pan} - {self.client_name}"
