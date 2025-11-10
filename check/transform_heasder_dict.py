def transform_dict(input_dict):
    """
    Transform a dictionary of categories with subcategories into
    a nested dictionary with status and rules set to True.

    Args:
        input_dict (dict): Dictionary in the form {cat: [subcats]}

    Returns:
        dict: Transformed dictionary
    """
    output_dict = {}
    for cat, subcats in input_dict.items():
        output_dict[cat] = {
            "status": True,
            "rules": {subcat: True for subcat in subcats}
        }
    return output_dict

# Example usage
input_data = {
    "cat1": ["subCat1_1", "subCat1_2", "subCat1_3"],
    "cat2": ["subCat2_1", "subCat2_2", "subCat2_3"]
}

result = transform_dict(input_data)
print(result)


# {
#  'cat1': {'status': True, 'rules': {'subCat1_1': True, 'subCat1_2': True, 'subCat1_3': True}},
#  'cat2': {'status': True, 'rules': {'subCat2_1': True, 'subCat2_2': True, 'subCat2_3': True}}
# }



def count_false_rules(nested_dict):
    """
    Count how many False values are present under 'rules' in a nested dictionary.

    Args:
        nested_dict (dict): Dictionary in the form 
            {cat: {"status": bool, "rules": {subcat: bool}}}

    Returns:
        int: Total number of False values under rules
    """
    return sum(
        1 for cat_data in nested_dict.values()
          for rule_value in cat_data["rules"].values()
          if not rule_value
    )

# Example usage
sample_dict = {
    "cat1": {"status": True, "rules": {"subCat1_1": True, "subCat1_2": False, "subCat1_3": True}},
    "cat2": {"status": False, "rules": {"subCat2_1": True, "subCat2_2": True, "subCat2_3": False}}
}

false_rules_count = count_false_rules(sample_dict)
print(false_rules_count)  # Output: 2



def update_category_status(nested_dict):
    """
    Update the category status based on its subcategories (rules).
    - If all rules are False, category status becomes False
    - If any rule is True, category status becomes True
    """
    for cat, cat_data in nested_dict.items():
        cat_data["status"] = any(cat_data["rules"].values())
    return nested_dict


def drop_false_entries(nested_dict):
    """
    Remove categories or subcategories that are False.
    - If category status is False, remove the category entirely
    - If a subcategory rule is False, remove that subcategory
    """
    new_dict = {}
    for cat, cat_data in nested_dict.items():
        # Filter only True rules
        filtered_rules = {k: v for k, v in cat_data["rules"].items() if v}
        if filtered_rules:  # keep category if there is any True rule
            new_dict[cat] = {
                "status": True,
                "rules": filtered_rules
            }
    return new_dict


# Example usage
sample_dict = {
    "cat1": {"status": True, "rules": {"subCat1_1": False, "subCat1_2": False, "subCat1_3": False}},
    "cat2": {"status": True, "rules": {"subCat2_1": True, "subCat2_2": False, "subCat2_3": True}},
    "cat3": {"status": True, "rules": {"subCat3_1": False, "subCat3_2": False}}
}

# Update category status based on rules
updated_dict = update_category_status(sample_dict)
print("Updated Status:", updated_dict)

# Drop False entries
cleaned_dict = drop_false_entries(updated_dict)
print("Cleaned Dict:", cleaned_dict)
