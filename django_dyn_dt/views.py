import os, json, math, random, string, base64

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.models import Q
from django.db.models.fields.related import RelatedField
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.db.models import CharField, DateField, IntegerField, FloatField, BooleanField


# Create your views here.
from django.views.decorators.csrf import csrf_exempt

from .helpers import Utils

from django.db.models.fields import DateField

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from django.conf import settings

DYNAMIC_DATATB = {}

try:
    DYNAMIC_DATATB = getattr(settings, 'DYNAMIC_DATATB')
except:
    pass

# TODO: 404 for wrong page number
def data_table_view(request, **kwargs):
    try:
        model_class = Utils.get_class(DYNAMIC_DATATB, kwargs.get('model_name'))
    except KeyError:
        return render(request, '404.html', status=404)
    headings = _get_headings(model_class)
    page_number = int(request.GET.get('page', 1))
    search_key = request.GET.get('search', '')
    entries = int(request.GET.get('entries', 10))

    if page_number < 1:
        return render(request, '404.html', status=404)

    filter_options = Q()
    for field in headings:
        filter_options = filter_options | Q(**{field + '__icontains': search_key})
    all_data = model_class.objects.filter(filter_options)
    data = all_data[(page_number - 1) * entries:page_number * entries]
    if all_data.count() != 0 and not 1 <= page_number <= math.ceil(all_data.count() / entries):
        return render(request, '404.html', status=404)
    
    field_types = []
    for field in model_class._meta.get_fields():
        if isinstance(field, DateField):
            field_types.append('date')
        elif isinstance(field, IntegerField):
            field_types.append('integer')
        elif isinstance(field, FloatField):
            field_types.append('float')
        elif isinstance(field, BooleanField):
            field_types.append('boolean')
        else:
            field_types.append('string')

    return render(request, 'index.html', context={
        'model_name': kwargs.get('model_name'),
        'display_name': model_class._meta.verbose_name or kwargs.get('model_name'),
        'headings': headings,
        'display_headings': _get_display_headings(model_class),
        'data': [["" if (val := getattr(record, heading)) is None else val for heading in headings] for record in data],
        'field_types': field_types,
        'total_pages': range(1, math.ceil(all_data.count() / entries) + 1),
        'has_prev': page_number > 1,
        'has_next': page_number < math.ceil(all_data.count() / entries),
        'current_page': page_number,
        'entries': entries,
        'search': search_key,
    })


@csrf_exempt
def add_record(request, **kwargs):
    try:
        model_manager = Utils.get_manager(DYNAMIC_DATATB, kwargs.get('model_name'))
    except KeyError:
        return JsonResponse({
            'message': 'This model is not activated or does not exist.',
            'success': False
        }, status=400)

    body = json.loads(request.body.decode("utf-8"))

    # Remove id field if it exists
    body.pop('id', None)

    for key, value in body.items():
        if value == '':
            body[key] = None

    try:
        model_class = Utils.get_class(DYNAMIC_DATATB, kwargs.get('model_name'))
        model_object = model_class(**body)
        model_object.full_clean()
        thing = model_manager.create(**body)
    except ValidationError as ve:
        errors = {field: error for field, error in ve.message_dict.items()}
        return JsonResponse({
            'detail': errors,
            'success': False
        }, status=400)
    except Exception as ve:
        return JsonResponse({
            'detail': str(ve),
            'success': False
        }, status=400)

    return JsonResponse({
        'id': thing.id,
        'message': 'Record Created.',
        'success': True
    }, status=200)


@csrf_exempt
def delete_record(request, **kwargs):
    try:
        model_manager = Utils.get_manager(DYNAMIC_DATATB, kwargs.get('model_name'))
    except KeyError:
        return JsonResponse({
            'message': 'This model is not activated or does not exist.',
            'success': False
        }, status=400)
    
    to_delete_id = kwargs.get('id')
    try:
        to_delete_object = model_manager.get(id=to_delete_id)
    except Exception:
        return JsonResponse({
            'message': 'Matching object not found.',
            'success': False
        }, status=404)
    
    if request.method == 'DELETE':
        to_delete_object.delete()
        return JsonResponse({
            'message': 'Record Deleted.',
            'success': True
        }, status=200)
    else:
        # Return the object data for confirmation modal
        data = {field.name: getattr(to_delete_object, field.name) for field in to_delete_object._meta.fields}
        return JsonResponse({
            'data': data,
            'message': 'Record Found.',
            'success': True
        }, status=200)


@csrf_exempt
def edit_record(request, **kwargs):
    try:
        model_class = Utils.get_class(DYNAMIC_DATATB, kwargs.get("model_name"))
    except KeyError:
        return JsonResponse(
            {"message": "This model is not activated or does not exist.", "success": False},
            status=400,
        )

    to_update_id = kwargs.get("id")
    body = json.loads(request.body.decode("utf-8"))

    try:
        model_object = model_class.objects.get(id=to_update_id)
    except ObjectDoesNotExist:
        return JsonResponse(
            {"message": "Object with the given ID does not exist.", "success": False},
            status=404,
        )

    for key, value in body.items():
        if value == '':
            value = None
        setattr(model_object, key, value)

    try:
        model_object.full_clean()
        model_object.save()
        return JsonResponse({"message": "Record Updated.", "success": True})
    except ValidationError as e:
        errors = {field: error for field, error in e.message_dict.items()}
        return JsonResponse({"detail": errors, "success": False}, status=400)
    except Exception as ve:
        return JsonResponse({"detail": str(ve), "success": False}, status=400)


@csrf_exempt
def export(request, **kwargs):
    try:
        model_class = Utils.get_class(DYNAMIC_DATATB, kwargs.get('model_name'))
    except KeyError:
        return render(request, '404.html', status=404)
    request_body = json.loads(request.body.decode('utf-8'))
    search_key = request_body.get('search', '')
    hidden = request_body.get('hidden_cols', [])
    export_type = request_body.get('type', 'csv')
    filter_options = Q()

    headings = list(_get_headings(model_class))
    for field in headings:
        field_name = field
        try:
            filter_options = filter_options | Q(**{field_name + '__icontains': search_key})
        except Exception as _:
            pass

    all_data = model_class.objects.filter(filter_options)
    table_data = []
    for data in all_data:
        this_row = []
        for heading in headings:
            this_row.append(getattr(data, heading))
        table_data.append(this_row)

    df = pd.DataFrame(
        table_data,
        columns=tuple(heading for heading in headings))
    if export_type == 'pdf':
        base64encoded = get_pdf(df)
    elif export_type == 'xlsx':
        base64encoded = get_excel(df)
    elif export_type == 'csv':
        base64encoded = get_csv(df)
    else:
        base64encoded = 'nothing'

    return HttpResponse(json.dumps({
        'content': base64encoded,
        'file_format': export_type,
        'success': True
    }), status=200)


def get_pdf(data_frame, ):
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.axis('tight')
    ax.axis('off')
    ax.table(cellText=data_frame.values, colLabels=data_frame.columns, loc='center',
             colLoc='center', )
    random_file_name = get_random_string(10) + '.pdf'
    pp = PdfPages(random_file_name)
    pp.savefig(fig, bbox_inches='tight')
    pp.close()
    bytess = read_file_and_remove(random_file_name)
    return base64.b64encode(bytess).decode('utf-8')


def get_excel(data_frame, ):
    random_file_name = get_random_string(10) + '.xlsx'

    data_frame.to_excel(random_file_name, index=False, header=True, encoding='utf-8')
    bytess = read_file_and_remove(random_file_name)
    return base64.b64encode(bytess).decode('utf-8')


def get_csv(data_frame, ):
    random_file_name = get_random_string(10) + '.csv'

    data_frame.to_csv(random_file_name, index=False, header=True, encoding='utf-8')
    bytess = read_file_and_remove(random_file_name)
    return base64.b64encode(bytess).decode('utf-8')


def read_file_and_remove(path):
    with open(path, 'rb') as file:
        bytess = file.read()
        file.close()

    # ths file pointer should be closed before removal
    os.remove(path)
    return bytess


def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def _get_headings(model_class, filter_relations=True):
    headings = []
    for field in model_class._meta.get_fields():
        if filter_relations and _is_relation_field(field):
            continue
        headings.append(field.name)
    return headings

def _get_display_headings(model_class, filter_relations=True):
    headings = []
    for field in model_class._meta.get_fields():
        if filter_relations and _is_relation_field(field):
            continue
        headings.append(field.verbose_name or field.name)
    return headings

def _is_relation_field(field):
    is_many_to_many_field = field.many_to_many is not None
    is_many_to_one_field = field.many_to_one is not None
    is_one_to_many_field = field.one_to_many is not None
    is_one_to_one_field = field.one_to_one is not None
    return is_many_to_many_field or is_many_to_one_field or is_one_to_many_field or is_one_to_one_field
