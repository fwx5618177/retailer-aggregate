package com.searetailer.api;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

@SpringBootTest
@ActiveProfiles("local")
class SeaRetailerApiApplicationTests {

    @Test
    void contextLoads() {
        // Verifies the application context loads successfully under the local profile.
    }
}
