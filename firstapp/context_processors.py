def user_context(request):
    """Context processor to provide current logged-in user to all templates."""
    user = request.session.get('user')
    if not user:
        # Default demo profile for display when accessing directly
        user = {
            'name': 'Madhu Manoj',
            'email': 'madhumanoj094@gmail.com',
            'phone': '6374934366',
            'city': 'Madurai',
            'state': 'Tamil Nadu',
            'role': 'citizen',
            'badge_number': 'TN-MD-101',
            'station': 'Vilakkuthoon PS, Madurai',
            'rank': 'Sub Inspector'
        }
    return {'current_user': user}
