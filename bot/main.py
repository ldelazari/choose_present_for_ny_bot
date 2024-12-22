import requests
from bs4 import BeautifulSoup
import psycopg2


BASE_URL = "https://www.vsemayki.ru/catalog/prikolnye_podarki/noviy_god"
CATEGORY_URL_FORMAT = "https://www.vsemayki.ru/catalog/view/{}/prikolnye_podarki/noviy_god"

categories = {
    'Мужская одежда': 'manwear',
    'Женская одежда': 'womanwear',
    'Детская одежда': 'childwear',
    'Головные уборы': 'headwear',
    'Сумки и рюкзаки': 'bags_and_backpacks',
    'Аксессуары': 'accessory',
    'Чехлы для телефонов': 'cases',
    'Домашний текстиль': 'textile',
    'Посуда': 'tableware',
    'Для интерьера': 'interior',
    'Для школы': 'school',
    'Для пляжа': 'beach',
    'Для спорта': 'sports_goods',
    'Сувениры и подарки': 'all_souvenirs',
    'Вся одежда': 'odezhda',
    'Одежда plus size': 'size_plus',
    'Распродажа': 'sale'
}

def get_db_connection():
    return psycopg2.connect(
        host="db",
        database="your_db",
        user="your_user",
        password="your_password"
    )


def get_products(category_slug, bot, chat_id):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT EXISTS(SELECT 1 FROM products WHERE category_slug = %s)", (category_slug,))
        result = cur.fetchone()

    if result and not result[0]:

        url = CATEGORY_URL_FORMAT.format(category_slug)
        response = requests.get(url)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        products = []

        catalog = soup.find("div", class_="styles_catalog_list__21cuV")
        if not catalog:
            bot.send_message(chat_id, f"Каталог товаров не найден для {category_slug}")
            return []

        items = catalog.find_all("div", class_="styles_catalog_list_card__3cP7c")
        for item in items:
            title_span = item.find("span", class_="styles_catalog_list_card__title__10J7P card__title")
            name = title_span.text.strip() if title_span else None

            price_span = item.find("span", class_="price")
            price = price_span.text.strip().replace("&nbsp;", "").replace("₽", "").strip() if price_span else None

            link_tag = item.find("a", class_="styles_link__3zI_G")
            link = "https://www.vsemayki.ru" + link_tag.get("href", "") if link_tag else None

            if name and price and link:
                insert_product(conn, name, price, link, category_slug)
                products.append({"name": name, "price": price, "link": link})

            if len(products) >= 5:
                break

        conn.close()
        return products
    else:
        conn.close()
        return get_products_from_db(category_slug)



def insert_product(conn, name, price, link, category_slug):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO products (name, price, link, category_slug) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (name, category_slug) DO NOTHING",
            (name, price, link, category_slug)
        )
    conn.commit()

def get_products_from_db(category_slug):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT name, price, link FROM products WHERE category_slug = %s", (category_slug,))
        products = cur.fetchall()
    conn.close()

    return [{"name": product[0], "price": product[1], "link": product[2]} for product in products]


def get_random_products_from_db():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT name, price, link FROM products ORDER BY RANDOM() LIMIT 5")
        products = cur.fetchall()
    conn.close()

    return [{"name": product[0], "price": product[1], "link": product[2]} for product in products]


if __name__ == "__main__":
    category = "manwear"
    print(get_products(category, None, None))

    print(get_random_products_from_db())
