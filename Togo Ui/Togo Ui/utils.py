import re

operation_name_map = {
    "ExportIFCTeklaAPI": "IFC",
    "CreateMeshGeometry": "Mesh",
    "CreateExchangeElementForPrimitive": "Primitives"
}
target_operations = list(operation_name_map.keys())

def extract_model_name(file_name):
    match = re.match(r"metrics_(.*?)_Demo.*\.csv", file_name)
    return match.group(1) if match else file_name

def match_operation(op_name):
    for key in target_operations:
        if key in op_name:
            return key
    return None
