import os
from io import BytesIO

from django.conf import settings
from docxtpl import DocxTemplate
from feewaiver.main_models import GlobalSettings


def create_feewaiver_pdf_contents(feewaiver, request):

    feewaiver_template = GlobalSettings.objects.get(key=GlobalSettings.KEY_FEEWAIVER_TEMPLATE_FILE)

    if feewaiver_template._file:
        path_to_template = feewaiver_template._file.path
    else:
        # Use default template file
        path_to_template = os.path.join(settings.BASE_DIR, 'feewaiver', 'static', 'feewaiver', 'fee_waiver_template.docx')

    doc = DocxTemplate(path_to_template)
    from feewaiver.serializers import FeeWaiverDocSerializer
    serializer_context = {
            "request": request,
            }
    context_obj = FeeWaiverDocSerializer(feewaiver, context=serializer_context)
    context = context_obj.data
    doc.render(context)

    temp_directory = settings.BASE_DIR + "/tmp/"
    try:
        os.stat(temp_directory)
    except:
        os.mkdir(temp_directory)

    f_name = temp_directory + 'feewaiver_' + str(feewaiver.id)
    new_doc_file = f_name + '.docx'
    new_pdf_file = f_name + '.pdf'
    doc.save(new_doc_file)
    os.system("libreoffice --headless --convert-to pdf " + new_doc_file + " --outdir " + temp_directory)

    file_contents = None
    with open(new_pdf_file, 'rb') as f:
        file_contents = f.read()
    os.remove(new_doc_file)
    os.remove(new_pdf_file)
    return file_contents

