import os
import pandas as pd
from flask import Flask, request, render_template
from matplotlib import pyplot as plt
from py2neo import Graph
from py2neo import Node, Relationship
from py2neo.matching import *

app = Flask(__name__)

#db_host = os.environ.get('NEO4J_HOST', 'localhost')
#db_port = os.environ.get('NEO4J_PORT', '7687')

#graph = Graph(f'neo4j://{db_host}:{db_port}', auth=("neo4j", "test"))
graph = Graph("bolt://44.198.56.56:7687", auth=("neo4j", "blinks-businesses-accessory"))
nodes = NodeMatcher(graph)


def reformat(value):
    if type(value) == str:
        value = value[0].upper() + value[1:].lower()
    return value


def make_relation(first_node, sec_node, kind):
    relation = Relationship(first_node, kind, sec_node)
    graph.create(relation)


def correct_values(val, dictionary):
    val = reformat(val)
    my_dict = {}
    for key, value in dictionary.items():
        key = reformat(key)
        value = reformat(value)
        my_dict[key] = value
    return val, my_dict


def create_node(val, dictionary):
    # change to same format for all kinds of input
    args, my_dict = correct_values(val, dictionary)
    node = Node(args, **my_dict)
    graph.create(node)
    return node


@app.route("/")
def route():
    #return '''<h1> hello world </h1>'''
    return render_template("home.html")


@app.route("/build_graph")
def build_graph():
    """
    This function build the graph according to the information of csv file.
    Starts with building the vertices, and then creating relationships.
    """
    df = pd.read_csv("friends_data.csv")
    df['apartment_number'] = df['apartment_number'].apply(
        lambda x: None if pd.isnull(x) else '{0:.0f}'.format(pd.to_numeric(x)))

    for index, row in df.iterrows():
        name, values = correct_values("Person", row[0:3].to_dict())
        node = nodes.match(name, **values).first()
        # if the person is not exist, create the person and the apartment
        if not node:
            person = create_node(name, values)
            apartment = create_node("Apartment", {'Number': row["apartment_number"]})
            make_relation(person, apartment, "Lives_in")

    for index, row in df.iterrows():
        print(row)
        name, values = correct_values("Person", row[0:3].to_dict())
        person = nodes.match(name, **values).first()
        if person:
            relation_types = ["parent_of", "married_to", "sibling"]
            for column in relation_types:
                if not pd.isnull(row[column]):
                    print(row[column])
                    name = row[column]
                    index = df[df["name"] == name].index
                    print(index)
                    index = index[0]
                    name, values = correct_values("Person", df.iloc[index][0:3].to_dict())
                    person2 = nodes.match(name, **values).first()
                    make_relation(person, person2, column)
    return '''<h1>The graph has been created successfully </h1>'''


'''******************************************************************************************************************'''


# In this section we give the user the option to create vertices or relationships with the information he give us.


@app.route("/create_person/<string:name>&<int:age>&<string:gender>", methods=["GET", "POST"])
def create_person(name, age, gender):
    """
    :param name: The name of the person as string.
    :param age: The age of the person as integer.
    :param gender: The gender of the person as string.
    :return: A message if it created this node or not.
    """
    if not nodes.match("Person", Name=name, Age=age, Gender=gender).first():
        person = Node("Person", Name=name, Age=age, Gender=gender)
        graph.create(person)
        return f" Node of person named {name} is successfully created! "
    return f"node of a person named {name} is already exist! "


@app.route("/create_apartment/<int:number>", methods=["GET", "POST"])
def create_apartment(number):
    """
    :param number: The apartment number as integer.
    :return: A message if it created this node or not.
    """
    if not nodes.match("Apartment", Number=number).first():
        apartment = Node("Apartment", Number=number)
        graph.create(apartment)
        return f" Node of apartment number {number} is successfully created! "
    return f"node of apartment number {number} is already exist! "


@app.route("/create_relationship/res", methods=["GET", "POST"])
def res():
    """
    This function gets two nodes that the user want to connect with a relationship.
    We can create only the following relations:
    Person - Lives in - Apartment.
    Person - parent_of - Person.
    Person - married_to - Person.
    Person - sibling - Person.
    otherwise it will return
    :return: A message of success if the relationship was legitimate, otherwise return an error message.
    """
    first = request.args.get('first_node')
    second = request.args.get('sec_node')
    rel = request.args.get('relationship')

    # if the user filled the information
    if request.method == "POST":
        name = request.form.get('Id')
        age = int(request.form.get('Age'))
        gender = request.form.get('Gender')

        if first == "Person" and second == "Apartment":
            number = int(request.form.get('Apartment'))
            if (nodes.match("Person", Name=name, Age=age, Gender=gender).first()) \
                    and (nodes.match("Apartment", Number=number).first()):

                person = nodes.match("Person", Name=name, Age=age, Gender=gender).first()
                apartment = nodes.match("Apartment", Number=number).first()
                if rel == "Lives_in":
                    relation = Relationship(person, rel, apartment)
                    graph.create(relation)
                    return '''<h1> Relationship of type {} is created</h1>'''.format(rel)
                else:
                    return '''<h1>This type of relationship cannot connect those two vertices </h1>'''.format(name, age,
                                                                                                              gender,
                                                                                                              number)
        else:
            if first == "Person" and second == "Person":
                name2 = request.form.get('Id2')
                age2 = int(request.form.get('Age2'))
                gender2 = request.form.get('Gender2')

                if (nodes.match("Person", Name=name, Age=age, Gender=gender).first()) and (
                        nodes.match("Person", Name=name2, Age=age2, Gender=gender2).first()):
                    person1 = nodes.match("Person", Name=name, Age=age, Gender=gender).first()
                    person2 = nodes.match("Person", Name=name2, Age=age2, Gender=gender2).first()
                    if rel != "Lives_in":
                        relation = Relationship(person1, rel, person2)
                        graph.create(relation)
                        return '''<h1> Relationship of type {} is created</h1>'''.format(rel)
                    else:
                        return '''<h1>This type of relationship cannot connect those two vertices  </h1>'''

        return '''<h1>You can not connect between these two vertices, please try again. </h1>'''
    else:
        if first == "Person" and second == "Apartment":
            return render_template('res_person_apartment.html')
        elif first == "Person" and second == "Person":
            return render_template('res_person_person.html')
        else:
            return '''<h1> You can not connect between these two vertices, please try again.</h1>'''


@app.route("/create_relationship", methods=["GET"])
def create_relationship():
    """
    :return: An html file for user input, which goes to /create_relationship/res for output.
    """
    return render_template('create_relationship.html')


'''****************************************************************************************************************'''


# The first query
@app.route("/query1", methods=["GET"])
def query1():
    """
     :return: The names of the roommates and the apartment number they are sharing
    """
    query = "MATCH(Person1:Person)-[:Lives_in]->(Apartment:Apartment)<-[:Lives_in]-(Person2:Person) " \
            "return Person1.Name,Person2.Name,Apartment.Number"
    data = graph.run(query).to_data_frame()
    data = data.drop_duplicates(subset='Apartment.Number', keep="last")
    # data.to_html('templates/query1.html')
    return render_template('query1.html')


@app.route("/query2", methods=["GET"])
def query2():
    """
    :return: The the oldest person in the group and his age
    """
    query = "MATCH (n:Person) RETURN n.Name, n.Age ORDER BY n.Age DESC"
    data = graph.run(query).to_data_frame()
    name = data["n.Name"][0]
    age = data["n.Age"][0]
    return '''<h1> {} is the oldest in the group, he is {} years old</h1>'''.format(name, age)


@app.route("/query3", methods=["GET"])
def query3():
    """
    :return: Returns a bar plot that represent the number of relationships of each relationship
    """
    result = {"relType": [], "count": []}
    relation_types = ["parent_of", "married_to", "sibling", "Lives_in"]
    for relation in relation_types:
        query = f"MATCH ()-[:`{relation}`]->() RETURN count(*) as count"
        count = graph.run(query).to_data_frame()["count"]
        count = count[0]
        result["relType"].append(relation)
        result["count"].append(count)
    df = pd.DataFrame(result)
    df.plot(kind='bar', x='relType', y='count', legend=None, color=['orange', 'olivedrab', 'dodgerblue', 'red'])
    plt.title("Relationships")
    plt.xlabel("Relationship Type")
    plt.ylabel("count")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('static/my_plot.png')
    return '<h1 style ="text-align: center"> Relationship distribution</h1>' \
           '<center><img src="static/my_plot.png" width=600 "></center>'


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
