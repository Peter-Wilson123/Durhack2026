from collections import Counter
from sqlalchemy import func, or_, select
from models import Interest, User, UserInterest, db


def find_new_interest(user: User) -> Interest | None:
    """
    Recommends a single new Interest object for `user`:
      1. Finds other users who share at least one interest with `user`, then
         picks the most common interest among that group that `user` doesn't have.
      2. Falls back to recommending an unjoined interest from the same Category
         topics as `user`'s existing interests.
    """
    if not user or not user.is_authenticated:
        return None

    my_interest_ids = {ui.interest_id for ui in user.user_interests}

    # If the user has no interests yet, return a random starter interest
    if not my_interest_ids:
        return db.session.scalar(select(Interest).order_by(func.random()).limit(1))

    # 1. Collaborative filtering: find other users sharing at least one interest
    similar_user_ids = list(
        db.session.scalars(
            select(UserInterest.user_id)
            .where(
                UserInterest.interest_id.in_(my_interest_ids),
                UserInterest.user_id != user.user_id,
            )
            .distinct()
        )
    )

    if similar_user_ids:
        candidate_ids = list(
            db.session.scalars(
                select(UserInterest.interest_id).where(
                    UserInterest.user_id.in_(similar_user_ids),
                    UserInterest.interest_id.notin_(my_interest_ids),
                )
            )
        )
        if candidate_ids:
            most_common_id, _ = Counter(candidate_ids).most_common(1)[0]
            return db.session.get(Interest, most_common_id)

    # 2. Category fallback: find another interest in the user's existing categories
    category_candidates: Counter[int] = Counter()
    for ui in user.user_interests:
        for category in ui.interest.categories:
            for candidate in category.interests:
                if candidate.interest_id not in my_interest_ids:
                    category_candidates[candidate.interest_id] += 1

    if category_candidates:
        best_category_id, _ = category_candidates.most_common(1)[0]
        return db.session.get(Interest, best_category_id)

    return None