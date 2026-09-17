export const HOTEL_NAME = 'Willow Park Residence'

export type AppLocale = 'pl' | 'en'

export type Messages = {
  hotelName: string
  documentTitle: string
  common: {
    skipToContent: string
    search: string
    from: string
    to: string
    cancel: string
    save: string
    filter: string
    loading: string
    tryAgain: string
    unexpectedError: string
    applicationError: string
    pageCrashed: string
    all: string
    optionalPhone: string
    email: string
    password: string
    darkMode: string
    lightMode: string
    language: string
    polish: string
    english: string
    restoringSession: string
    weekdays: [string, string, string, string, string, string, string]
  }
  nav: {
    publicAria: string
    adminAria: string
    search: string
    myBooking: string
    staff: string
    adminBrand: string
    dashboard: string
    reservations: string
    guests: string
    rates: string
    events: string
    roomTypes: string
    rooms: string
    logOut: string
  }
  validation: {
    checkInRequired: string
    checkInInvalid: string
    checkOutRequired: string
    checkOutInvalid: string
    guestsInt: string
    guestsMin: string
    guestsMax: string
    checkInPast: string
    checkInLead: string
    checkOutAfter: string
    stayMax: string
    firstName: string
    lastName: string
    email: string
    payment: string
    codeRequired: string
    roomTypeRequired: string
    ratePlanRequired: string
    priceRequired: string
    priceRange: string
    priceBand: string
    pickRoomType: string
  }
  status: {
    CONFIRMED: string
    CHECKED_IN: string
    CHECKED_OUT: string
    CANCELLED: string
    NO_SHOW: string
  }
  booking: {
    homeTitle: string
    homeSubtitle: string
    manageCta: string
    searchTitle: string
    searchSubmit: string
    checkIn: string
    checkOut: string
    guests: string
    emptyDatesTitle: string
    emptyDatesDesc: string
    availabilityError: string
    noRoomsTitle: string
    noRoomsDesc: string
    roomMeta: string
    nightlyBar: string
    ratePlans: string
    refundable: string
    nonRefundable: string
    breakfast: string
    select: string
    checkoutTitle: string
    checkoutMissing: string
    searchAgain: string
    guestsCount: string
    roomFilled: string
    bookingFailed: string
    reserving: string
    payAndBook: string
    backToResults: string
    guestDetails: string
    firstName: string
    lastName: string
    mockPayment: string
    mockPaymentHint: string
    authorizePayment: string
    authorizePaymentAria: string
    confirmationTitle: string
    confirmationHint: string
    confirmationError: string
    confirmationEmptyTitle: string
    confirmationEmptyDesc: string
    home: string
    manageTitle: string
    manageHint: string
    confirmationCode: string
    findBooking: string
    lookupError: string
    manageEmptyTitle: string
    manageEmptyDesc: string
    alreadyCancelled: string
    nonRefundableNotice: string
    cancelling: string
    cancelBooking: string
    cancelNonRefundable: string
    cancelFailed: string
    cancelSuccess: string
    summaryTitle: string
    code: string
    room: string
    rate: string
    priceBreakdown: string
    total: string
  }
  admin: {
    loginTitle: string
    loginFailed: string
    signingIn: string
    signIn: string
    incompleteToken: string
    dashboardTitle: string
    dashboardSubtitle: string
    kpisError: string
    occupancyToday: string
    roomsHint: string
    arrivals: string
    departures: string
    mtdRevenue: string
    chartTitle: string
    chartError: string
    chartEmptyTitle: string
    chartEmptyDesc: string
    occupancy: string
    occupancyPct: string
    adr: string
    adrPln: string
    reservationsTitle: string
    walkIn: string
    walkInTitle: string
    walkInCreateFailed: string
    walkInSubmit: string
    status: string
    search: string
    reservationsError: string
    actionError: string
    reservationsEmptyTitle: string
    reservationsEmptyDesc: string
    colCode: string
    colGuest: string
    colDates: string
    colRoom: string
    colStatus: string
    colAmount: string
    detailTitle: string
    detailError: string
    priceBreakdown: string
    guestsTitle: string
    guestsSearch: string
    guestsError: string
    guestsEmptyTitle: string
    guestsEmptyDesc: string
    colName: string
    colEmail: string
    colPhone: string
    ratesTitle: string
    roomType: string
    month: string
    refreshPrices: string
    ratesError: string
    ratesEmptyTitle: string
    ratesEmptyDesc: string
    demand: string
    manualOverride: string
    typeRange: string
    pricePln: string
    removeOverride: string
    saveManual: string
    refreshFailed: string
    eventsTitle: string
    eventsSubtitle: string
    eventsError: string
    eventsEmptyTitle: string
    eventsEmptyDesc: string
    demandTitle: string
    demandError: string
    demandEmpty: string
    colEvent: string
    colImpact: string
    colConfidence: string
    colRationale: string
    roomTypesTitle: string
    addRoomType: string
    roomsTitle: string
    addRoom: string
    edit: string
    delete: string
    active: string
    code: string
    name: string
    capacity: string
    basePrice: string
    minPrice: string
    maxPrice: string
    amenities: string
    saveFailed: string
    roomNumber: string
    floor: string
    roomStatus: string
    notes: string
    available: string
    outOfService: string
    adults: string
    ratePlan: string
  }
}

export const messagesByLocale: Record<AppLocale, Messages> = {
  pl: {
    hotelName: HOTEL_NAME,
    documentTitle: HOTEL_NAME,
    common: {
      skipToContent: 'Przejdź do treści',
      search: 'Szukaj',
      from: 'Od',
      to: 'Do',
      cancel: 'Anuluj',
      save: 'Zapisz',
      filter: 'Filtruj',
      loading: 'Ładowanie…',
      tryAgain: 'Spróbuj ponownie',
      unexpectedError: 'Nieoczekiwany błąd interfejsu',
      applicationError: 'Błąd aplikacji',
      pageCrashed: 'Strona uległa awarii podczas renderowania.',
      all: 'Wszystkie',
      optionalPhone: 'Telefon (opcjonalnie)',
      email: 'E-mail',
      password: 'Hasło',
      darkMode: 'Tryb ciemny',
      lightMode: 'Tryb jasny',
      language: 'Język',
      polish: 'Polski',
      english: 'English',
      restoringSession: 'Przywracanie sesji',
      weekdays: ['Pn', 'Wt', 'Śr', 'Cz', 'Pt', 'So', 'Nd'],
    },
    nav: {
      publicAria: 'Nawigacja publiczna',
      adminAria: 'Nawigacja panelu',
      search: 'Szukaj',
      myBooking: 'Moja rezerwacja',
      staff: 'Personel',
      adminBrand: `${HOTEL_NAME} — Panel`,
      dashboard: 'Pulpit',
      reservations: 'Rezerwacje',
      guests: 'Goście',
      rates: 'Taryfy',
      events: 'Wydarzenia',
      roomTypes: 'Typy pokoi',
      rooms: 'Pokoje',
      logOut: 'Wyloguj',
    },
    validation: {
      checkInRequired: 'Wybierz datę zameldowania',
      checkInInvalid: 'Nieprawidłowa data zameldowania',
      checkOutRequired: 'Wybierz datę wymeldowania',
      checkOutInvalid: 'Nieprawidłowa data wymeldowania',
      guestsInt: 'Liczba gości musi być liczbą całkowitą',
      guestsMin: `Minimum ${1} gość`,
      guestsMax: `Maximum ${10} gości`,
      checkInPast: 'Zameldowanie nie może być w przeszłości',
      checkInLead: 'Zameldowanie najwyżej 365 dni do przodu',
      checkOutAfter: 'Wymeldowanie musi być po zameldowaniu',
      stayMax: 'Pobyt najwyżej 30 nocy',
      firstName: 'Podaj imię',
      lastName: 'Podaj nazwisko',
      email: 'Podaj poprawny e-mail',
      payment: 'Potwierdź mockową płatność, aby dokończyć rezerwację',
      codeRequired: 'Podaj kod potwierdzenia',
      roomTypeRequired: 'Wybierz typ pokoju',
      ratePlanRequired: 'Wybierz plan taryfowy',
      priceRequired: 'Podaj poprawną cenę',
      priceRange: 'Cena musi być w zakresie min–max PLN',
      priceBand: 'Wymagane: minPrice ≤ basePrice ≤ maxPrice',
      pickRoomType: 'Wybierz typ pokoju',
    },
    status: {
      CONFIRMED: 'Potwierdzona',
      CHECKED_IN: 'Zameldowana',
      CHECKED_OUT: 'Wymeldowana',
      CANCELLED: 'Anulowana',
      NO_SHOW: 'No-show',
    },
    booking: {
      homeTitle: HOTEL_NAME,
      homeSubtitle:
        'Sprawdź dostępność i zarezerwuj pobyt. Ceny pochodzą bezpośrednio z kalendarza taryf hotelu.',
      manageCta: 'Zarządzaj rezerwacją',
      searchTitle: 'Wyszukaj pobyt',
      searchSubmit: 'Szukaj dostępności',
      checkIn: 'Zameldowanie',
      checkOut: 'Wymeldowanie',
      guests: 'Goście',
      emptyDatesTitle: 'Wybierz daty pobytu',
      emptyDatesDesc: 'Uzupełnij zameldowanie, wymeldowanie i liczbę gości, aby zobaczyć oferty.',
      availabilityError: 'Nie udało się pobrać dostępności.',
      noRoomsTitle: 'Brak wolnych pokoi',
      noRoomsDesc:
        'Dla wybranych dat nie ma dostępnych typów pokoi. Zmień zakres dat lub liczbę gości.',
      roomMeta: 'Kod {code} · do {capacity} osób · zostało {roomsLeft} pokoi',
      nightlyBar: 'Cena za noc (BAR z API)',
      ratePlans: 'Plany taryfowe',
      refundable: 'Zwrotna',
      nonRefundable: 'Bezzwrotna',
      breakfast: 'śniadanie',
      select: 'Wybierz',
      checkoutTitle: 'Potwierdzenie i płatność',
      checkoutMissing: 'Brakuje wyboru pokoju lub dat. Wróć do wyszukiwania.',
      searchAgain: 'Szukaj ponownie',
      guestsCount: '{count} gości',
      roomFilled: 'Wybrany pokój właśnie się zapełnił. Wybierz inną ofertę.',
      bookingFailed: 'Rezerwacja nie powiodła się.',
      reserving: 'Rezerwuję…',
      payAndBook: 'Zapłać (mock) i zarezerwuj',
      backToResults: 'Wróć do wyników',
      guestDetails: 'Dane gościa',
      firstName: 'Imię',
      lastName: 'Nazwisko',
      mockPayment: 'Mockowa płatność',
      mockPaymentHint: 'Demo nie obciąża karty. Potwierdź autoryzację kwoty z odpowiedzi API.',
      authorizePayment: 'Autoryzuję mockową płatność {amount}',
      authorizePaymentAria: 'Potwierdź mockową płatność',
      confirmationTitle: 'Rezerwacja potwierdzona',
      confirmationHint: 'Zachowaj kod potwierdzenia — razem z e-mailem pozwala zarządzać pobytem.',
      confirmationError: 'Nie udało się wczytać rezerwacji.',
      confirmationEmptyTitle: 'Brak kodu potwierdzenia',
      confirmationEmptyDesc: 'Otwórz link z e-maila lub wróć do wyszukiwania.',
      home: 'Strona główna',
      manageTitle: 'Zarządzaj rezerwacją',
      manageHint: 'Podaj kod potwierdzenia i e-mail użyty przy rezerwacji.',
      confirmationCode: 'Kod potwierdzenia',
      findBooking: 'Znajdź rezerwację',
      lookupError: 'Nie znaleziono rezerwacji dla podanych danych.',
      manageEmptyTitle: 'Wyszukaj rezerwację',
      manageEmptyDesc:
        'Wpisz kod potwierdzenia i e-mail, aby zobaczyć szczegóły i ewentualnie anulować pobyt.',
      alreadyCancelled: 'Ta rezerwacja jest już anulowana.',
      nonRefundableNotice: 'Taryfa bezzwrotna — anulowanie online jest niedostępne.',
      cancelling: 'Anulowanie…',
      cancelBooking: 'Anuluj rezerwację',
      cancelNonRefundable: 'Taryfa tej rezerwacji nie pozwala na anulowanie online.',
      cancelFailed: 'Anulowanie nie powiodło się.',
      cancelSuccess: 'Rezerwacja została anulowana.',
      summaryTitle: 'Podsumowanie rezerwacji',
      code: 'Kod',
      room: 'Pokój',
      rate: 'taryfa',
      priceBreakdown: 'Rozbicie cen z API',
      total: 'Razem',
    },
    admin: {
      loginTitle: 'Logowanie personelu',
      loginFailed: 'Logowanie nieudane — sprawdź e-mail i hasło.',
      signingIn: 'Logowanie…',
      signIn: 'Zaloguj',
      incompleteToken: 'Niekompletna odpowiedź tokenu',
      dashboardTitle: 'Pulpit',
      dashboardSubtitle: 'KPI dnia biznesowego{date} + 30-dniowy wykres occupancy / ADR.',
      kpisError: 'Nie udało się wczytać KPI.',
      occupancyToday: 'Obłożenie dziś',
      roomsHint: '{occupied} / {sellable} pokoi',
      arrivals: 'Przyloty',
      departures: 'Wyloty',
      mtdRevenue: 'Przychód MTD',
      chartTitle: 'Obłożenie i ADR — ostatnie 30 dni',
      chartError: 'Nie udało się wczytać szeregu czasowego.',
      chartEmptyTitle: 'Brak danych wykresu',
      chartEmptyDesc: 'Brak punktów w oknie 30 dni.',
      occupancy: 'Obłożenie',
      occupancyPct: 'Obłożenie %',
      adr: 'ADR',
      adrPln: 'ADR PLN',
      reservationsTitle: 'Rezerwacje',
      walkIn: 'Walk-in',
      walkInTitle: 'Walk-in / rezerwacja recepcji',
      walkInCreateFailed: 'Nie udało się utworzyć rezerwacji',
      walkInSubmit: 'Utwórz rezerwację',
      status: 'Status',
      search: 'Szukaj',
      reservationsError: 'Błąd listy rezerwacji',
      actionError: 'Akcja nieudana — przywrócono poprzedni stan.',
      reservationsEmptyTitle: 'Brak rezerwacji',
      reservationsEmptyDesc: 'Zmień filtry statusu / dat / wyszukiwania.',
      colCode: 'Kod',
      colGuest: 'Gość',
      colDates: 'Daty',
      colRoom: 'Pokój',
      colStatus: 'Status',
      colAmount: 'Kwota',
      detailTitle: 'Szczegóły rezerwacji',
      detailError: 'Nie wczytano szczegółów',
      priceBreakdown: 'Rozbicie cen',
      guestsTitle: 'Goście',
      guestsSearch: 'Szukaj (imię / e-mail)',
      guestsError: 'Błąd listy gości',
      guestsEmptyTitle: 'Brak gości',
      guestsEmptyDesc: 'Zmień zapytanie lub dodaj rezerwację, aby pojawił się gość.',
      colName: 'Imię i nazwisko',
      colEmail: 'E-mail',
      colPhone: 'Telefon',
      ratesTitle: 'Kalendarz taryf',
      roomType: 'Typ pokoju',
      month: 'Miesiąc',
      refreshPrices: 'Odśwież ceny',
      ratesError: 'Błąd kalendarza',
      ratesEmptyTitle: 'Brak wpisów kalendarza',
      ratesEmptyDesc:
        'Dla wybranego typu i miesiąca nie ma dni z ceną — używany będzie base price.',
      demand: 'popyt',
      manualOverride: 'Ręczne nadpisanie — {date}',
      typeRange: 'Zakres typu',
      pricePln: 'Cena PLN',
      removeOverride: 'Usuń override',
      saveManual: 'Zapisz MANUAL',
      refreshFailed: 'Odświeżenie nieudane',
      eventsTitle: 'Wydarzenia i popyt',
      eventsSubtitle:
        'Dane z proxy PMS → pricing-service (faza 8). Do czasu podłączenia listy pozostają puste.',
      eventsError: 'Błąd listy wydarzeń',
      eventsEmptyTitle: 'Brak wydarzeń',
      eventsEmptyDesc: 'Proxy zwróci pustą listę do czasu podłączenia pricing-service.',
      demandTitle: 'Wskaźnik popytu',
      demandError: 'Błąd wskaźników popytu',
      demandEmpty: 'Brak punktów popytu w zakresie.',
      colEvent: 'Wydarzenie',
      colImpact: 'Wpływ',
      colConfidence: 'Pewność',
      colRationale: 'Uzasadnienie',
      roomTypesTitle: 'Typy pokoi',
      addRoomType: 'Dodaj typ',
      roomsTitle: 'Pokoje',
      addRoom: 'Dodaj pokój',
      edit: 'Edytuj',
      delete: 'Usuń',
      active: 'Aktywny',
      code: 'Kod',
      name: 'Nazwa',
      capacity: 'Pojemność',
      basePrice: 'Cena bazowa',
      minPrice: 'Cena min',
      maxPrice: 'Cena max',
      amenities: 'Udogodnienia',
      saveFailed: 'Zapis nieudany',
      roomNumber: 'Numer pokoju',
      floor: 'Piętro',
      roomStatus: 'Status',
      notes: 'Notatki',
      available: 'Dostępny',
      outOfService: 'Wyłączony',
      adults: 'Goście',
      ratePlan: 'Plan taryfowy',
    },
  },
  en: {
    hotelName: HOTEL_NAME,
    documentTitle: HOTEL_NAME,
    common: {
      skipToContent: 'Skip to content',
      search: 'Search',
      from: 'From',
      to: 'To',
      cancel: 'Cancel',
      save: 'Save',
      filter: 'Filter',
      loading: 'Loading…',
      tryAgain: 'Try again',
      unexpectedError: 'Unexpected UI error',
      applicationError: 'Application error',
      pageCrashed: 'The page crashed while rendering.',
      all: 'All',
      optionalPhone: 'Phone (optional)',
      email: 'Email',
      password: 'Password',
      darkMode: 'Dark mode',
      lightMode: 'Light mode',
      language: 'Language',
      polish: 'Polski',
      english: 'English',
      restoringSession: 'Restoring session',
      weekdays: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    },
    nav: {
      publicAria: 'Public navigation',
      adminAria: 'Admin navigation',
      search: 'Search',
      myBooking: 'My booking',
      staff: 'Staff',
      adminBrand: `${HOTEL_NAME} — Admin`,
      dashboard: 'Dashboard',
      reservations: 'Reservations',
      guests: 'Guests',
      rates: 'Rates',
      events: 'Events',
      roomTypes: 'Room types',
      rooms: 'Rooms',
      logOut: 'Log out',
    },
    validation: {
      checkInRequired: 'Choose a check-in date',
      checkInInvalid: 'Invalid check-in date',
      checkOutRequired: 'Choose a check-out date',
      checkOutInvalid: 'Invalid check-out date',
      guestsInt: 'Guest count must be a whole number',
      guestsMin: 'Minimum 1 guest',
      guestsMax: 'Maximum 10 guests',
      checkInPast: 'Check-in cannot be in the past',
      checkInLead: 'Check-in at most 365 days ahead',
      checkOutAfter: 'Check-out must be after check-in',
      stayMax: 'Stay at most 30 nights',
      firstName: 'Enter first name',
      lastName: 'Enter last name',
      email: 'Enter a valid email',
      payment: 'Confirm the mock payment to complete the booking',
      codeRequired: 'Enter the confirmation code',
      roomTypeRequired: 'Choose a room type',
      ratePlanRequired: 'Choose a rate plan',
      priceRequired: 'Enter a valid price',
      priceRange: 'Price must be within the min–max PLN range',
      priceBand: 'Required: minPrice ≤ basePrice ≤ maxPrice',
      pickRoomType: 'Choose a room type',
    },
    status: {
      CONFIRMED: 'Confirmed',
      CHECKED_IN: 'Checked in',
      CHECKED_OUT: 'Checked out',
      CANCELLED: 'Cancelled',
      NO_SHOW: 'No-show',
    },
    booking: {
      homeTitle: HOTEL_NAME,
      homeSubtitle:
        'Check availability and book your stay. Prices come directly from the hotel rate calendar.',
      manageCta: 'Manage booking',
      searchTitle: 'Search stay',
      searchSubmit: 'Search availability',
      checkIn: 'Check-in',
      checkOut: 'Check-out',
      guests: 'Guests',
      emptyDatesTitle: 'Choose stay dates',
      emptyDatesDesc: 'Enter check-in, check-out and guest count to see offers.',
      availabilityError: 'Could not load availability.',
      noRoomsTitle: 'No rooms available',
      noRoomsDesc: 'No room types are free for these dates. Change the dates or guest count.',
      roomMeta: 'Code {code} · up to {capacity} guests · {roomsLeft} rooms left',
      nightlyBar: 'Nightly price (BAR from API)',
      ratePlans: 'Rate plans',
      refundable: 'Refundable',
      nonRefundable: 'Non-refundable',
      breakfast: 'breakfast',
      select: 'Select',
      checkoutTitle: 'Confirm and pay',
      checkoutMissing: 'Missing room or dates. Go back to search.',
      searchAgain: 'Search again',
      guestsCount: '{count} guests',
      roomFilled: 'That room just sold out. Pick another offer.',
      bookingFailed: 'Booking failed.',
      reserving: 'Booking…',
      payAndBook: 'Pay (mock) and book',
      backToResults: 'Back to results',
      guestDetails: 'Guest details',
      firstName: 'First name',
      lastName: 'Last name',
      mockPayment: 'Mock payment',
      mockPaymentHint: 'This demo does not charge a card. Confirm authorization of the API amount.',
      authorizePayment: 'I authorize the mock payment of {amount}',
      authorizePaymentAria: 'Confirm mock payment',
      confirmationTitle: 'Booking confirmed',
      confirmationHint:
        'Keep your confirmation code — with your email it lets you manage the stay.',
      confirmationError: 'Could not load the booking.',
      confirmationEmptyTitle: 'Missing confirmation code',
      confirmationEmptyDesc: 'Open the email link or return to search.',
      home: 'Home',
      manageTitle: 'Manage booking',
      manageHint: 'Enter the confirmation code and email used at booking.',
      confirmationCode: 'Confirmation code',
      findBooking: 'Find booking',
      lookupError: 'No booking found for these details.',
      manageEmptyTitle: 'Look up a booking',
      manageEmptyDesc: 'Enter the confirmation code and email to view details or cancel.',
      alreadyCancelled: 'This booking is already cancelled.',
      nonRefundableNotice: 'Non-refundable rate — online cancellation is unavailable.',
      cancelling: 'Cancelling…',
      cancelBooking: 'Cancel booking',
      cancelNonRefundable: 'This rate plan does not allow online cancellation.',
      cancelFailed: 'Cancellation failed.',
      cancelSuccess: 'The booking was cancelled.',
      summaryTitle: 'Booking summary',
      code: 'Code',
      room: 'Room',
      rate: 'rate',
      priceBreakdown: 'Price breakdown from API',
      total: 'Total',
    },
    admin: {
      loginTitle: 'Staff login',
      loginFailed: 'Login failed — check email and password.',
      signingIn: 'Signing in…',
      signIn: 'Sign in',
      incompleteToken: 'Incomplete token response',
      dashboardTitle: 'Dashboard',
      dashboardSubtitle: 'Business-day KPIs{date} + 30-day occupancy / ADR chart.',
      kpisError: 'Could not load KPIs.',
      occupancyToday: 'Occupancy today',
      roomsHint: '{occupied} / {sellable} rooms',
      arrivals: 'Arrivals',
      departures: 'Departures',
      mtdRevenue: 'MTD revenue',
      chartTitle: 'Occupancy and ADR — last 30 days',
      chartError: 'Could not load the time series.',
      chartEmptyTitle: 'No chart data',
      chartEmptyDesc: 'No points in the 30-day window.',
      occupancy: 'Occupancy',
      occupancyPct: 'Occupancy %',
      adr: 'ADR',
      adrPln: 'ADR PLN',
      reservationsTitle: 'Reservations',
      walkIn: 'Walk-in',
      walkInTitle: 'Walk-in / front-desk booking',
      walkInCreateFailed: 'Could not create the reservation',
      walkInSubmit: 'Create reservation',
      status: 'Status',
      search: 'Search',
      reservationsError: 'Reservations list error',
      actionError: 'Action failed — previous state restored.',
      reservationsEmptyTitle: 'No reservations',
      reservationsEmptyDesc: 'Change status / date / search filters.',
      colCode: 'Code',
      colGuest: 'Guest',
      colDates: 'Dates',
      colRoom: 'Room',
      colStatus: 'Status',
      colAmount: 'Amount',
      detailTitle: 'Reservation details',
      detailError: 'Could not load details',
      priceBreakdown: 'Price breakdown',
      guestsTitle: 'Guests',
      guestsSearch: 'Search (name / email)',
      guestsError: 'Guests list error',
      guestsEmptyTitle: 'No guests',
      guestsEmptyDesc: 'Change the query or add a reservation to create a guest.',
      colName: 'Full name',
      colEmail: 'Email',
      colPhone: 'Phone',
      ratesTitle: 'Rate calendar',
      roomType: 'Room type',
      month: 'Month',
      refreshPrices: 'Refresh prices',
      ratesError: 'Calendar error',
      ratesEmptyTitle: 'No calendar entries',
      ratesEmptyDesc: 'No priced days for this type and month — base price will be used.',
      demand: 'demand',
      manualOverride: 'Manual override — {date}',
      typeRange: 'Type range',
      pricePln: 'Price PLN',
      removeOverride: 'Remove override',
      saveManual: 'Save MANUAL',
      refreshFailed: 'Refresh failed',
      eventsTitle: 'Events and demand',
      eventsSubtitle:
        'Data via PMS proxy → pricing-service (phase 8). Lists stay empty until wired.',
      eventsError: 'Events list error',
      eventsEmptyTitle: 'No events',
      eventsEmptyDesc: 'Proxy returns an empty list until pricing-service is connected.',
      demandTitle: 'Demand indicator',
      demandError: 'Demand indicators error',
      demandEmpty: 'No demand points in range.',
      colEvent: 'Event',
      colImpact: 'Impact',
      colConfidence: 'Confidence',
      colRationale: 'Rationale',
      roomTypesTitle: 'Room types',
      addRoomType: 'Add room type',
      roomsTitle: 'Rooms',
      addRoom: 'Add room',
      edit: 'Edit',
      delete: 'Delete',
      active: 'Active',
      code: 'Code',
      name: 'Name',
      capacity: 'Capacity',
      basePrice: 'Base price',
      minPrice: 'Min price',
      maxPrice: 'Max price',
      amenities: 'Amenities',
      saveFailed: 'Save failed',
      roomNumber: 'Room number',
      floor: 'Floor',
      roomStatus: 'Status',
      notes: 'Notes',
      available: 'Available',
      outOfService: 'Out of service',
      adults: 'Guests',
      ratePlan: 'Rate plan',
    },
  },
}
