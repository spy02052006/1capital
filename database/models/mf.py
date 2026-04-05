"""
Mutual Fund Fact Model
Represents mutual fund transactions: subscription, redemption, trail fees, etc.
"""
from django.db import models


class MFact(models.Model):
    """
    Mutual Fund transaction fact table.
    Records MF purchases, redemptions, and associated fees/charges.
    """
    
    # Transaction identifiers
    folio_check = models.CharField(max_length=50, db_index=True,
                                   help_text="Folio check number")
    investor_name = models.CharField(max_length=255, db_index=True)
    pan_no = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    euin = models.CharField(max_length=50, null=True, blank=True, db_index=True,
                           help_text="MF distributor EUIN")
    
    # Transaction details
    transaction_type = models.CharField(max_length=10, null=True, blank=True,
                                       help_text="P=Purchase, R=Redemption, S=Switch")
    units = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True,
                              help_text="NAV or transaction rate")
    
    # Fee period details
    fee_from_date = models.DateField(null=True, blank=True, db_index=True)
    fee_to_date = models.DateField(null=True, blank=True)
    days_in_fee_period = models.IntegerField(null=True, blank=True)
    
    # Trail fee details
    trail_fee_from_date = models.DateField(null=True, blank=True)
    trail_fee_to_date = models.DateField(null=True, blank=True)
    
    # Commission/charges
    brokerage = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    avg_assets = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True,
                                     help_text="Average assets under management for fee calculation")
    
    # Fee classification
    fee_type = models.CharField(max_length=10, null=True, blank=True,
                               help_text="A=Annual, Q=Quarterly, M=Monthly, etc.")
    fee_description = models.CharField(max_length=500, null=True, blank=True,
                                       help_text="Detailed description of fee type and scheme")
    
    # Scheme/Fund details
    scheme_short_name = models.CharField(max_length=255, null=True, blank=True, db_index=True,
                                        help_text="Mutual fund scheme name")
    reference_no = models.CharField(max_length=50, null=True, blank=True, unique=True)
    
    # Channel/Intermediary
    broker_code = models.CharField(max_length=50, null=True, blank=True, db_index=True,
                                  help_text="ARN or broker code")
    sub_broker = models.CharField(max_length=50, null=True, blank=True)
    sub_broker_detail = models.CharField(max_length=50, null=True, blank=True)
    ter_location = models.CharField(max_length=10, null=True, blank=True,
                                    help_text="Transfer agent location code")
    
    # Dates
    trade_date = models.DateField(null=True, blank=True, db_index=True,
                                 help_text="Transaction trade date")
    processing_date = models.DateField(null=True, blank=True, db_index=True,
                                      help_text="Fee processing date")
    
    # Flags
    adjustment_flag = models.CharField(max_length=5, null=True, blank=True,
                                      help_text="Y/N - indicates if this is an adjustment entry")
    switch_flag = models.CharField(max_length=5, null=True, blank=True,
                                  help_text="Y/N - indicates if this is a switch transaction")
    
    # Metadata
    source_file = models.CharField(max_length=255, null=True, blank=True,
                                   help_text="Excel filename this record was loaded from")
    loaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    row_hash = models.CharField(max_length=64, null=True, blank=True, unique=True, db_index=True,
                                help_text="SHA256 hash of row for duplicate detection")
    
    class Meta:
        db_table = 'mf_fact'
        indexes = [
            models.Index(fields=['folio_check', 'trade_date']),
            models.Index(fields=['investor_name']),
            models.Index(fields=['scheme_short_name']),
            models.Index(fields=['broker_code']),
        ]
        verbose_name = 'MF Fact'
        verbose_name_plural = 'MF Facts'
        ordering = ['-processing_date', 'folio_check']
    
    def __str__(self):
        return f"{self.folio_check} - {self.investor_name} - {self.scheme_short_name}"
