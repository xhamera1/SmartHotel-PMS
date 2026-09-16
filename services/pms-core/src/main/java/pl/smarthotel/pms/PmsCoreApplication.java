package pl.smarthotel.pms;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class PmsCoreApplication {

    public static void main(String[] args) {
        SpringApplication.run(PmsCoreApplication.class, args);
    }
}
