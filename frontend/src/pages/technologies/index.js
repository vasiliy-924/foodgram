import { Title, Container, Main } from '../../components'
import styles from './styles.module.css'
import MetaTags from 'react-meta-tags'

const Technologies = () => {
  
  return <Main>
    <MetaTags>
      <title>Технологии</title>
      <meta name="description" content="Фудграм - Технологии" />
      <meta property="og:title" content="Технологии" />
    </MetaTags>
    
    <Container>
      <h1 className={styles.title}>Технологии</h1>
      <div className={styles.content}>
        <div>
          <h2 className={styles.subtitle}>Технологии, которые применены в этом проекте:</h2>
          <div className={styles.text}>
            <ul className={styles.textItem}>
              <li className={styles.textItem}>Python 3</li>
              <li className={styles.textItem}>Django {process.env.REACT_APP_DJANGO_VERSION || '5.x'}</li>
              <li className={styles.textItem}>Django REST Framework</li>
              <li className={styles.textItem}>Djoser</li>
              <li className={styles.textItem}>django-filter</li>
              <li className={styles.textItem}>PostgreSQL</li>
              <li className={styles.textItem}>Gunicorn</li>
              <li className={styles.textItem}>Nginx</li>
              <li className={styles.textItem}>Docker, docker-compose</li>
              <li className={styles.textItem}>React, React Router</li>
              <li className={styles.textItem}>Token-based auth (DRF authtoken)</li>
              <li className={styles.textItem}>dotenv</li>
              <li className={styles.textItem}>psycopg2-binary</li>
              <li className={styles.textItem}>Pillow</li>
            </ul>
          </div>
        </div>
      </div>
      
    </Container>
  </Main>
}

export default Technologies

