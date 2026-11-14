from models import Interest, User, UserInterest


def find_users_by_interest(query: str, exclude_user_id: int | None = None) -> list[User]:
	"""
	Searches for users with an interest matching `query` (case-insensitive).
	Returns a Python list of User objects (empty list if nothing matches).
	"""

	clean_query = query.strip()
	print(clean_query)
	if not clean_query:

		return []

	users_query = (
		User.query.join(UserInterest)
		.join(Interest)
		.filter(Interest.interest_name.ilike(f"%{clean_query}%"))
	)

	if exclude_user_id is not None:
		users_query = users_query.filter(User.user_id != exclude_user_id)
	print(users_query.distinct().all())
	return users_query.distinct().all()
