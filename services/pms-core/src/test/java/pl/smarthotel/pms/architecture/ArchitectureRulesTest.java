package pl.smarthotel.pms.architecture;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;

import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.junit.AnalyzeClasses;
import com.tngtech.archunit.junit.ArchTest;
import com.tngtech.archunit.lang.ArchRule;

@AnalyzeClasses(
        packages = "pl.smarthotel.pms",
        importOptions = ImportOption.DoNotIncludeTests.class)
class ArchitectureRulesTest {

    @ArchTest
    static final ArchRule controllersDoNotTouchRepositories = noClasses()
            .that()
            .haveSimpleNameEndingWith("Controller")
            .should()
            .dependOnClassesThat()
            .haveSimpleNameEndingWith("Repository")
            .because("controllers talk to services, not repositories (package-by-feature)");

    @ArchTest
    static final ArchRule noJavaUtilDate = noClasses()
            .should()
            .dependOnClassesThat()
            .haveFullyQualifiedName("java.util.Date")
            .because("use java.time via the injectable Clock");

    @ArchTest
    static final ArchRule noJavaSqlDate = noClasses()
            .should()
            .dependOnClassesThat()
            .haveFullyQualifiedName("java.sql.Date")
            .because("use java.time.LocalDate instead of java.sql.Date");

    @ArchTest
    static final ArchRule noJavaSqlTimestamp = noClasses()
            .should()
            .dependOnClassesThat()
            .haveFullyQualifiedName("java.sql.Timestamp")
            .because("use java.time.Instant instead of java.sql.Timestamp");

    @ArchTest
    static final ArchRule servicesDoNotImportControllers = noClasses()
            .that()
            .haveSimpleNameEndingWith("Service")
            .should()
            .dependOnClassesThat()
            .haveSimpleNameEndingWith("Controller")
            .because("services must not depend on controllers (inverted dependency)");

    @ArchTest
    static final ArchRule entitiesDoNotLeakIntoControllers = noClasses()
            .that()
            .haveSimpleNameEndingWith("Controller")
            .should()
            .dependOnClassesThat()
            .haveSimpleNameEndingWith("Entity")
            .because("controllers work with DTOs/records, never with JPA entities directly");

    @ArchTest
    static final ArchRule pricingPackageIsolation = noClasses()
            .that()
            .resideInAPackage("..pricing..")
            .should()
            .dependOnClassesThat()
            .resideInAnyPackage("..reservations..", "..guests..", "..auth..", "..dashboard..")
            .because("pricing integration package should not depend on other domain packages");
}
