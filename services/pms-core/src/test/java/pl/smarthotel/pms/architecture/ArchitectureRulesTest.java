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
}
