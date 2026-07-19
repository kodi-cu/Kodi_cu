"""Herramientas para el sistema multi-agente"""

from .file_utils import (
    find_files,
    get_file_info,
    format_size,
    ensure_directory,
    supported_extensions,
    is_supported_file
)

from .pdf_utils import (
    extract_text_from_pdf,
    extract_metadata_from_pdf,
    get_pdf_images,
    is_pdf_valid
)

from .odt_utils import (
    extract_text_from_odt,
    extract_text_from_ods,
    extract_text_from_odp,
    get_odf_metadata,
    is_odf_valid
)

from .vision_utils import (
    encode_image_to_base64,
    create_vision_message,
    analyze_image_with_llm,
    extract_text_from_image,
    describe_chart_or_graph,
    is_image_file
)

__all__ = [
    # File utils
    'find_files',
    'get_file_info',
    'format_size',
    'ensure_directory',
    'supported_extensions',
    'is_supported_file',
    
    # PDF utils
    'extract_text_from_pdf',
    'extract_metadata_from_pdf',
    'get_pdf_images',
    'is_pdf_valid',
    
    # ODT utils
    'extract_text_from_odt',
    'extract_text_from_ods',
    'extract_text_from_odp',
    'get_odf_metadata',
    'is_odf_valid',
    
    # Vision utils
    'encode_image_to_base64',
    'create_vision_message',
    'analyze_image_with_llm',
    'extract_text_from_image',
    'describe_chart_or_graph',
    'is_image_file'
]
