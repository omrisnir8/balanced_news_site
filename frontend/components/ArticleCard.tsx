import React from 'react';
import styles from '../styles/ArticleCard.module.css';
import { Link2 } from 'lucide-react';

export interface SourceArticle {
    source_name: string;
    location: string;
    political_orientation: string;
    known_bias: string;
    url: string;
    published_at?: string;
    titles: {
        native: string;
        en: string;
        he: string;
    };
    bias_warnings: {
        en: string;
        he: string;
    };
}

export interface ClusterProps {
    id: number;
    titles: {
        en: string;
        he: string;
    };
    summaries: {
        en: string;
        he: string;
    };
    timestamp: string;
    category: string;
    sources: SourceArticle[];
}

function getInitials(name: string) {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
}

export default function ArticleCard({ cluster, language }: { cluster: ClusterProps, language: "en" | "he" | "native" }) {
    const isRtl = language === 'he' || (language === 'native' && cluster.titles.he);
    const displayTitle = (language === 'en') ? cluster.titles.en : cluster.titles.he;
    const displaySummary = (language === 'en') ? cluster.summaries.en : cluster.summaries.he;

    return (
        <div className={styles.container} dir={isRtl ? 'rtl' : 'ltr'}>
            {/* Level 1 & 2: Headline and Glass Summary Card */}
            <article className={styles.headlineCard}>
                <div className={styles.headlineLabel}>
                    {language === 'he' ? 'כותרת ממוצעת (Heavy Sans):' : 'Average Headline (Heavy Sans):'}
                </div>
                <h2 className={styles.title}>{displayTitle}</h2>

                <div className={styles.summaryCard}>
                    <div className={styles.summaryLabel}>
                        {language === 'he' ? 'פרספקטיבה השוואתית (SF Pro)' : 'Comparative Perspective (SF Pro)'}
                    </div>
                    <p className={styles.summary}>{displaySummary}</p>
                </div>
            </article>

            {/* Level 3: Sources List Card */}
            <div className={styles.sourcesCard}>
                {cluster.sources.map((source, idx) => {
                    const sourceBias = language === 'he' ? source.bias_warnings.he : source.bias_warnings.en;
                    const biasText = `${source.political_orientation} • ${source.known_bias}`;

                    return (
                        <div key={idx}>
                            <a
                                href={source.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className={styles.sourceItem}
                            >
                                <div className={styles.sourceLogo}>
                                    {getInitials(source.source_name)}
                                </div>
                                <div className={styles.sourceInfo}>
                                    <div className={styles.sourceHeader}>
                                        {source.source_name} • {source.political_orientation}
                                    </div>
                                    <div className={styles.sourceMeta}>
                                        [{source.source_name}] • {source.political_orientation}
                                    </div>
                                </div>
                                <Link2 size={18} className={styles.linkIcon} />
                            </a>
                            {sourceBias && (
                                <div className={styles.biasWarning}>
                                    {sourceBias}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
