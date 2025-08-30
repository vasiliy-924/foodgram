import { Title, Container, Main } from '../../components'
import styles from './styles.module.css'
import MetaTags from 'react-meta-tags'

const About = ({ updateOrders, orders }) => {
  
  return <Main>
    <MetaTags>
      <title>О проекте</title>
      <meta name="description" content="Фудграм - О проекте" />
      <meta property="og:title" content="О проекте" />
    </MetaTags>
    
    <Container>
      <h1 className={styles.title}>О проекте</h1>
      <div className={styles.content}>
        <div>
          <h2 className={styles.subtitle}>Что это за сайт?</h2>
          <div className={styles.text}>
            <p className={styles.textItem}>
              «Фудграм» — веб‑приложение для публикации и хранения кулинарных рецептов.
            </p>
            <p className={styles.textItem}>
              Пользователи регистрируются, создают рецепты с фотографиями, ингредиентами и тегами, могут редактировать и удалять свои публикации.
            </p>
            <p className={styles.textItem}>
              Доступны избранное, подписки на авторов и список покупок: рецепты можно добавлять/удалять из избранного и корзины с любой страницы списка.
            </p>
            <p className={styles.textItem}>
              Список покупок выгружается файлом, при этом одноимённые ингредиенты суммируются. Поиск ингредиентов работает по вхождению в начало названия.
            </p>
          </div>
        </div>
        <aside>
          <h2 className={styles.additionalTitle}>
            Ссылки
          </h2>
          <div className={styles.text}>
            <p className={styles.textItem}>
              Автор проекта: Петров Василий
            </p>
            <p className={styles.textItem}>
              GitHub: <a href="https://github.com/vasiliy-924" target="_blank" rel="noreferrer" className={styles.textLink}>github.com/vasiliy-924</a>
            </p>
            <p className={styles.textItem}>
              Email: <a href="mailto:vasiliy924vip@yandex.ru" className={styles.textLink}>vasiliy924vip@yandex.ru</a>
            </p>
            <p className={styles.textItem}>
              Телефон: <a href="tel:+79373804794" className={styles.textLink}>+7 (937) 380‑47‑94</a>
            </p>
            <p className={styles.textItem}>
              Telegram: <a href="https://t.me/thunderbasil" target="_blank" rel="noreferrer" className={styles.textLink}>@thunderbasil</a>
            </p>
            <div className={styles.qrWrapper}>
              <img src="/images/telegram-qr.png" alt="QR‑код Telegram @thunderbasil" className={styles.qr} />
            </div>
          </div>
        </aside>
      </div>
      
    </Container>
  </Main>
}

export default About

