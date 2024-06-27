from django.core.validators import ValidationError

def validate_file_size(file):
    max_size_in_kb = 2 * 1024 * 1024

    if file.size > max_size_in_kb:
        raise ValidationError(f'File size should be less than {max_size_in_kb / 1024} MB')