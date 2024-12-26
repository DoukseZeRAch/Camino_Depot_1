from graphviz import Digraph

def generate_db_diagram(db_models):
    dot = Digraph(comment='Database Diagram')

    # Ajouter les nœuds pour chaque modèle
    for model_name, model_info in db_models.items():
        fields = '\n'.join([f"{field['name']}: {field['type']}" for field in model_info['fields']])
        dot.node(model_name, f"{model_name}\n{fields}")

    # Ajouter les relations
    for model_name, model_info in db_models.items():
        for relation in model_info['relations']:
            dot.edge(model_name, relation['model'], label=relation['type'])

    # Enregistrer le diagramme
    dot.render('database_diagram.gv', view=True)
