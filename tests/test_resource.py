from tests.api import UserResource

from lesoon_common.utils.base import random_alpha_numeric


class TestLesoonResource:

    def test_page_get(self, db):
        users = self.generate_random_user(25)
        db.session.bulk_insert_mappings(mapper=UserResource.__model__,
                                        mappings=users)
        res, total = UserResource.page_get()
        assert total == 25
        assert res == users

    def test_create_one(self, db):
        users = self.generate_random_user(1)
        UserResource.create_one(users[0])
        db.session.commit()
        res, total = UserResource.page_get()
        assert total == 1
        assert res == users

    def test_create_many(self, db):
        users = self.generate_random_user(10)
        UserResource.create_many(users)
        db.session.commit()
        res, total = UserResource.page_get()
        assert total == 10
        assert res == users

    def test_update(self, db):
        user = self.generate_random_user(1)[0]
        UserResource.create(user)

        user['login_name'] = 'test_update'
        res = UserResource.update(user)
        assert res == user

    def test_remove(self, db):
        users = self.generate_random_user(20)
        UserResource.create(users)

        UserResource.remove([user['id'] for user in users[:10]])

        res, total = UserResource.page_get()
        assert total == 10
        assert res == users[10:]

    @staticmethod
    def generate_random_user(size: int):
        users = list()
        for i in range(size):
            user = {
                'id': str(i),
                'login_name': random_alpha_numeric(10),
                'user_name': random_alpha_numeric(10),
            }
            users.append(user)
        return users
