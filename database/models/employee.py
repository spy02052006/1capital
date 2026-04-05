"""
Employee Dimension Model
Represents employee/RM master data: ID, name, PAN, wire code, manager hierarchy
"""
from django.db import models


class EmployeeDim(models.Model):
    """
    Employee/Relationship Manager dimension table.
    Includes manager hierarchy information for organizational structure.
    """
    
    # Employee identifiers
    employee_id = models.IntegerField(unique=True, db_index=True,
                                      help_text="Unique employee ID")
    name = models.CharField(max_length=255, db_index=True)
    pan = models.CharField(max_length=50, null=True, blank=True, unique=True, db_index=True,
                          help_text="PAN number of the employee")
    
    # Organization hierarchy
    manager_id = models.IntegerField(null=True, blank=True, db_index=True,
                                     help_text="Employee ID of the manager (for hierarchy)")
    
    # Codes/Identifiers
    wire_code = models.CharField(max_length=50, null=True, blank=True, unique=True, db_index=True,
                                help_text="Wire/branch code assigned to employee")
    employee_code = models.CharField(max_length=50, null=True, blank=True, unique=True, db_index=True,
                                     help_text="Employee code (sometimes called employee id)")
    
    # Metadata
    source_file = models.CharField(max_length=255, null=True, blank=True,
                                   help_text="Excel filename this record was loaded from")
    loaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    row_hash = models.CharField(max_length=64, null=True, blank=True, unique=True, db_index=True,
                                help_text="SHA256 hash of row for duplicate detection")
    
    class Meta:
        db_table = 'employee_dim'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['wire_code']),
        ]
        verbose_name = 'Employee Dimension'
        verbose_name_plural = 'Employee Dimensions'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.employee_code} - {self.name}" if self.employee_code else f"{self.employee_id} - {self.name}"
