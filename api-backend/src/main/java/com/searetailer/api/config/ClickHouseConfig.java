package com.searetailer.api.config;

import com.clickhouse.jdbc.ClickHouseDataSource;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.jdbc.core.JdbcTemplate;

import javax.sql.DataSource;
import java.sql.SQLException;
import java.util.Properties;

@Configuration
public class ClickHouseConfig {

    @Configuration
    @Profile("!local")
    static class ProductionClickHouseConfig {

        @Value("${clickhouse.url}")
        private String clickHouseUrl;

        @Value("${clickhouse.username}")
        private String clickHouseUsername;

        @Value("${clickhouse.password}")
        private String clickHousePassword;

        @Bean(name = "clickHouseDataSource")
        public DataSource clickHouseDataSource() throws SQLException {
            Properties properties = new Properties();
            properties.setProperty("user", clickHouseUsername);
            properties.setProperty("password", clickHousePassword);
            properties.setProperty("socket_timeout", "30000");
            properties.setProperty("connect_timeout", "10000");
            return new ClickHouseDataSource(clickHouseUrl, properties);
        }

        @Bean(name = "clickHouseJdbcTemplate")
        public JdbcTemplate clickHouseJdbcTemplate(@Qualifier("clickHouseDataSource") DataSource ds) {
            JdbcTemplate template = new JdbcTemplate(ds);
            template.setQueryTimeout(30);
            return template;
        }
    }

    /**
     * Local profile: connect to the DuckDB file produced by the data pipeline.
     * DuckDB JDBC speaks standard SQL, so repositories use ANSI SQL that works
     * on both DuckDB (local) and ClickHouse (production).
     */
    @Configuration
    @Profile("local")
    static class LocalClickHouseConfig {

        @Value("${duckdb.path:../data-pipeline/data/pipeline.duckdb}")
        private String duckdbPath;

        @Bean(name = "clickHouseDataSource")
        public DataSource duckDbDataSource() {
            org.springframework.jdbc.datasource.DriverManagerDataSource ds =
                    new org.springframework.jdbc.datasource.DriverManagerDataSource();
            ds.setDriverClassName("org.duckdb.DuckDBDriver");
            ds.setUrl("jdbc:duckdb:" + duckdbPath);
            return ds;
        }

        @Bean(name = "clickHouseJdbcTemplate")
        public JdbcTemplate clickHouseJdbcTemplate(@Qualifier("clickHouseDataSource") DataSource ds) {
            return new JdbcTemplate(ds);
        }
    }
}
