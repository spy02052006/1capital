"""
Brokerage Fact Model
Represents equity brokerage transactions: cash, futures, options, commodities, etc.
"""
from django.db import models


class BrokerageFact(models.Model):
    """
    Brokerage transaction data for equity, derivatives, and commodities.
    One record per client per wire code per date.
    """
    
    # Core transaction identifiers
    client_code = models.CharField(max_length=50, db_index=True)
    wire_code = models.CharField(max_length=50, db_index=True)
    transaction_date = models.DateField(db_index=True)
    
    # Cash segment
    cash_delivery = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    cash_intraday = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    cash_total = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Derivatives segment
    futures = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    options = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    commodity = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Turnover metrics - Equity Cash
    equity_cash_intraday_turnover = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    equity_cash_delivery_turnover = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    total_equity_cash_turnover = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    
    # Turnover metrics - Equity Derivatives
    equity_futures_turnover = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    equity_options_turnover = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    total_equity_fno_turnover = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    total_equity_turnover = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    
    # Turnover metrics - Other segments
    currency_turnover = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    commodity_turnover = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    total_turnover = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    
    # VAS (Value Added Services)
    equity_vas = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    commodity_vas = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    total_vas_subscription = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    equity_vas_reversal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    commodity_vas_reversal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    total_vas_reversal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Summary
    total_brokerage = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Metadata
    source_file = models.CharField(max_length=255, null=True, blank=True, help_text="Excel filename this record was loaded from")
    loaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    row_hash = models.CharField(max_length=64, null=True, blank=True, unique=True, db_index=True, 
                                 help_text="SHA256 hash of row for duplicate detection")
    
    class Meta:
        db_table = 'brokerage_fact'
        indexes = [
            models.Index(fields=['client_code', 'transaction_date']),
            models.Index(fields=['wire_code', 'transaction_date']),
            models.Index(fields=['transaction_date']),
        ]
        verbose_name = 'Brokerage Fact'
        verbose_name_plural = 'Brokerage Facts'
        ordering = ['-transaction_date', 'client_code']
    
    def __str__(self):
        return f"{self.client_code} - {self.wire_code} - {self.transaction_date}"
