import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from store.models import Category, SubCategory, \
    Product, Article, Parameter, Customer, Order


@pytest.mark.django_db
class TestViews:

    @pytest.fixture(autouse=True)
    def setup_class(self):
        self.client = Client()
        user = User.objects.create_superuser(
            username='test_admin', password='12345'
        )
        self.client.force_login(user)

        Parameter.objects.create(name='FREE_GIFT', value='800')
        Parameter.objects.create(name='FREE_DELIVERY', value='2500')
        Parameter.objects.create(name='DELIVERY_COURIER_COST', value='450')

        category = Category.objects.create(name='Category1', slug='cat1')
        subcategory = SubCategory.objects.create(
            name='Subcategory1',
            category=category, slug='subcat1'
        )
        Product.objects.create(title='Product1',
                               category=category,
                               subcategory=subcategory,
                               image='test_image.jpg',
                               price=100,
                               slug='pro1')
        Article.objects.create(title='Test', name='Test', slug='test')
        customer = Customer.objects.create(user=user)
        self.order = Order.carts.create(owner=customer,
                                        delivery_type='delivery_spb')

    def test_index(self):
        response = self.client.get(reverse('welcome'))
        assert response.status_code == 200

    def test_store(self):
        response = self.client.get(reverse('store'))
        assert response.status_code == 200

    def test_article(self):
        response = self.client.get(reverse('article', kwargs={'slug': 'test'}))
        assert response.status_code == 200

    def test_search(self):
        data = {'p': '1'}
        response = self.client.get(reverse('search'), data=data)
        assert response.status_code == 200

    def test_product_detail(self):
        response = self.client.get(reverse('product_detail',
                                           kwargs={'slug': 'pro1'}))
        assert response.status_code == 200

    def test_subcategory(self):
        response = self.client.get(reverse('subcategory_detail',
                                           kwargs={'slug': 'subcat1'}))
        assert response.status_code == 200

    def test_category(self):
        response = self.client.get(reverse('category_detail',
                                           kwargs={'slug': 'cat1'}))
        assert response.status_code == 200

    def test_gifts(self):
        response = self.client.get(reverse('gifts'))
        assert response.status_code == 200

    def test_cart(self):
        response = self.client.get(reverse('cart'))
        assert response.status_code == 200

    def test_login(self):
        response = self.client.get(reverse('login'))
        assert response.status_code == 200

    def test_registration(self):
        response = self.client.get(reverse('registration'))
        assert response.status_code == 200

    def test_profile(self):
        response = self.client.get(reverse('profile'))
        assert response.status_code == 200

    """
    TEST VIEWS
    redirects, query parameters
    """

    def test_logout(self):
        response = self.client.get(reverse('logout'))
        assert response.status_code == 302
        assert response['Location'] == reverse('welcome')

    def test_add_to_cart(self):
        response = self.client.get(reverse('add_to_cart',
                                           kwargs={'slug': 'pro1'}))

        # if the product is added correctly we redirect
        assert response.status_code == 302
        assert response['Location'] == reverse('product_detail',
                                               kwargs={'slug': 'pro1'})

    # def test_checkout(self):
    #     """ не срабатывает: order не передается """
    #
    #     order = self.order
    #     print(order)
    #     data = {'delivery_type': 'delivery_spb'}
    #     response = self.client.post(reverse('checkout'), data=data)
    #     assert response.status_code == 200

    # def test_bank_payment(self):
    #     response = self.client.get(reverse('bank_payment'))
    #     assert response.status_code == 200
    #
    # def test_make_order(self):
    #     response = self.client.get(reverse('make-order'))
    #     assert response.status_code == 200
