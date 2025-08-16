from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
import os

property_bp = Blueprint('property', __name__)

# Folder for uploaded property images
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --------------------------------------------------
# Add Property
# --------------------------------------------------
@property_bp.route('/add_property', methods=['GET', 'POST'])
def add_property():
    if 'username' not in session:
        return redirect(url_for('auth.login'))

    db = current_app.config['db']
    properties_collection = db['properties']

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        rent = request.form.get('rent')
        deposit = request.form.get('deposit')
        property_type = request.form.get('property_type')

        # ----- multiple image upload -----
        image_files = request.files.getlist('images')
        image_paths = []
        for img in image_files:
            if img and img.filename != "":
                filename = secure_filename(img.filename)
                path = os.path.join(UPLOAD_FOLDER, filename)
                img.save(path)
                image_paths.append(path)

        properties_collection.insert_one({
            'username': session['username'],
            'title': title,
            'description': description,
            'rent': rent,
            'deposit': deposit,
            'property_type': property_type,
            'images': image_paths
        })

        return redirect(url_for('property.list_properties'))

    return render_template('add_property.html')


# --------------------------------------------------
# List Properties
# --------------------------------------------------
@property_bp.route('/properties')
def list_properties():
    db = current_app.config['db']
    properties_collection = db['properties']

    q = request.args.get('q', '').strip()
    prop_type = request.args.get('property_type', '').strip()

    query = {}
    if q:
        query['$or'] = [
            {'title': {'$regex': q, '$options': 'i'}},
            {'description': {'$regex': q, '$options': 'i'}}
        ]
    if prop_type:
        query['property_type'] = prop_type

    properties = list(properties_collection.find(query))
    return render_template('home.html', properties=properties, q=q, prop_type=prop_type)
# --------------------------------------------------
# Property Detail (no chat here)
# --------------------------------------------------
@property_bp.route('/property/<property_id>')
def view_property(property_id):
    db = current_app.config['db']
    properties_collection = db['properties']
    prop = properties_collection.find_one({'_id': ObjectId(property_id)})
    if not prop:
        return "Property not found", 404

    return render_template('property_detail.html', prop=prop)


# --------------------------------------------------
# User-to-User Chat (not related to property)
# --------------------------------------------------
@property_bp.route('/chat/<other_user>', methods=['GET', 'POST'])
def user_chat(other_user):
    if 'username' not in session:
        return redirect(url_for('auth.login'))

    current_user = session['username']
    db = current_app.config['db']
    messages_collection = db['messages']

    # Send message
    if request.method == 'POST':
        text = request.form.get('message')
        messages_collection.insert_one({
            'from_user': current_user,
            'to_user': other_user,
            'message': text
        })

    # Load conversation
    msgs = list(messages_collection.find({
        '$or': [
            {'from_user': current_user, 'to_user': other_user},
            {'from_user': other_user, 'to_user': current_user}
        ]
    }))

    return render_template(
        'chat.html',
        messages=msgs,
        other_user=other_user
    )


# --------------------------------------------------
# List All Conversations (My Chats)
# --------------------------------------------------
@property_bp.route('/my_chats')
def my_chats():
    if 'username' not in session:
        return redirect(url_for('auth.login'))

    current_user = session['username']
    db = current_app.config['db']
    messages_collection = db['messages']

    # Find all distinct users the current user talked to or received from
    conversations = messages_collection.aggregate([
        {'$match': {
            '$or': [
                {'from_user': current_user},
                {'to_user': current_user}
            ]
        }},
        {'$project': {
            'other': {
                '$cond': [
                    {'$eq': ['$from_user', current_user]},
                    '$to_user',
                    '$from_user'
                ]
            }
        }},
        {'$group': {'_id': '$other'}}
    ])

    users = [c['_id'] for c in conversations]

    return render_template('my_chats.html', users=users)
