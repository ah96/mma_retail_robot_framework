(define (domain retail-recommendation)
  (:requirements :strips :typing :negative-preconditions)
  (:types customer product)
  (:predicates
    (customer ?u - customer)
    (product ?p - product)
    (trousers ?p - product)
    (available ?p - product)
    (premium-item ?p - product)
    (comfort-priority ?u - customer)
    (budget-sensitive ?u - customer)
    (under-budget ?p - product ?u - customer)
    (upsell-rejected ?u - customer)
    (commercial-intent-disclosed ?p - product)
    (recommended ?u - customer ?p - product)
    (recommendation-made ?u - customer)
    (explained ?u - customer ?p - product)
    (alternative-offered ?u - customer)
  )

  (:action disclose-commercial-intent
    :parameters (?u - customer ?p - product)
    :precondition (and (customer ?u) (product ?p) (premium-item ?p))
    :effect (and (commercial-intent-disclosed ?p))
  )

  (:action recommend-budget-trousers
    :parameters (?u - customer ?p - product)
    :precondition (and
      (customer ?u)
      (product ?p)
      (trousers ?p)
      (available ?p)
      (comfort-priority ?u)
      (under-budget ?p ?u)
    )
    :effect (and (recommended ?u ?p) (recommendation-made ?u))
  )

  (:action recommend-premium-trousers
    :parameters (?u - customer ?p - product)
    :precondition (and
      (customer ?u)
      (product ?p)
      (trousers ?p)
      (available ?p)
      (premium-item ?p)
      (not (budget-sensitive ?u))
      (not (upsell-rejected ?u))
      (commercial-intent-disclosed ?p)
    )
    :effect (and (recommended ?u ?p) (recommendation-made ?u))
  )

  (:action explain-recommendation
    :parameters (?u - customer ?p - product)
    :precondition (and (recommended ?u ?p))
    :effect (and (explained ?u ?p))
  )

  (:action offer-alternative
    :parameters (?u - customer)
    :precondition (and (recommendation-made ?u))
    :effect (and (alternative-offered ?u))
  )
)
