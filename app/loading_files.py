from pprint import pprint

import yaml

# from app.data import get_main_params, get_other_params
from app.models import MainParameters, ProductParameters


def upload_yaml(file):
    read_data = yaml.load(file, Loader=yaml.FullLoader)
    # pprint(read_data)
    return read_data


def download_yaml(company, get_products):
    price_dict = dict(company=company.name, products=[])
    for i in get_products:
        main_params = MainParameters.objects.filter(product=i.product).first()
        if not main_params:
            main_params = MainParameters(color=None,
                                         weight=0,
                                         height=0,
                                         length=0,
                                         width=0,
                                         warranty=0,
                                         manufacturer=None,
                                         country=None,)
        other_params = ProductParameters.objects.filter(product=i.product)
        price_dict['products'].append(dict(article_number=i.product.article_number,
                                     name=i.product.name,
                                     category=dict(id=i.product.subcategory.id,
                                                   category=i.product.subcategory.category,
                                                   subcategory=i.product.subcategory.subcategory,
                                                    ),
                                     description=i.product.description,
                                     price=i.price,
                                     price_rrc=i.price_rrc,
                                     quantity=i.quantity,
                                     main_params=dict(color=main_params.color,
                                                      weight=main_params.weight,
                                                      height=main_params.height,
                                                      length=main_params.length,
                                                      width=main_params.width,
                                                      warranty=main_params.warranty,
                                                      manufacturer=main_params.manufacturer,
                                                      country=main_params.country,
                                                      ),
                                     parameters={y.category_parameters.name: y.value for y in other_params},
                                     ))
    pprint(price_dict)
    # path = 'static/yaml_files/new.yml'
    with open(f'static/yaml_files/price_{company.id}.yml', 'w+', encoding="utf-8") as file:
        yaml.dump(price_dict, file, allow_unicode=True)
        # return f'/{path}'
